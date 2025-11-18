from rest_framework import viewsets, permissions, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Bill, Category
from .serializers import BillSerializer, CategorySerializer
from .categorization_service import BillCategorizationService
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Sum, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return Bill.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        # Categorization is now handled in the serializer
        bill = serializer.save()
    
    @action(detail=True, methods=['post'])
    def recategorize(self, request, pk=None):
        """Manually recategorize a bill"""
        bill = self.get_object()
        category_id = request.data.get('category_id')
        
        try:
            category = Category.objects.get(id=category_id)
            categorization_service = BillCategorizationService()
            categorization_service.learn_from_user_correction(bill, category)
            
            serializer = self.get_serializer(bill)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=400)
    
    @action(detail=False, methods=['post'])
    def bulk_categorize(self, request):
        """Bulk categorize uncategorized bills"""
        categorization_service = BillCategorizationService()
        count = categorization_service.bulk_categorize_bills(user=request.user)
        return Response({'categorized_count': count})
    
    @action(detail=False, methods=['post'])
    def recategorize(self, request):
        """Recategorize specific bills by bill_ids"""
        bill_ids = request.data.get('bill_ids', [])
        
        if not bill_ids:
            return Response({'error': 'bill_ids is required'}, status=400)
        
        categorization_service = BillCategorizationService()
        bills = Bill.objects.filter(id__in=bill_ids, user=request.user)
        
        categorized_count = 0
        for bill in bills:
            try:
                categorization_service.categorize_bill(bill)
                categorized_count += 1
            except Exception as e:
                logger.error(f"Error recategorizing bill {bill.id}: {e}")
        
        return Response({
            'success': True,
            'categorized_count': categorized_count,
            'total': len(bills)
        })
    
    @action(detail=False, methods=['get'])
    def categories_summary(self, request):
        """Get bills summary by category"""
        summary = Bill.objects.filter(user=request.user).values(
            'category__name', 'category__type', 'category__color'
        ).annotate(
            total_amount=Sum('amount'),
            bill_count=Count('id')
        ).order_by('-total_amount')
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def spending_trends(self, request):
        """Monthly spending trends"""
        from django.db.models import Q
        from datetime import datetime, timedelta
        import calendar
        
        # Get last 12 months of data
        today = datetime.now()
        twelve_months_ago = today - timedelta(days=365)
        
        monthly_data = []
        for i in range(12):
            month_start = datetime(today.year, today.month, 1) - timedelta(days=30*i)
            month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
            
            monthly_total = Bill.objects.filter(
                user=request.user,
                created_at__range=[month_start, month_end],
                amount__isnull=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'total': float(monthly_total)
            })
        
        return Response(monthly_data[::-1])  # Reverse to show oldest first
    
    @action(detail=False, methods=['get'])
    def top_vendors(self, request):
        """Top spending vendors"""
        top_vendors = Bill.objects.filter(
            user=request.user,
            vendor__isnull=False,
            amount__isnull=False
        ).values('vendor').annotate(
            total_spent=Sum('amount'),
            bill_count=Count('id')
        ).order_by('-total_spent')[:10]
        
        return Response(top_vendors)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Dashboard overview statistics"""
        from datetime import datetime, timedelta
        
        today = datetime.now()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # Current month stats
        this_month_total = Bill.objects.filter(
            user=request.user,
            created_at__gte=this_month_start,
            amount__isnull=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Last month stats  
        last_month_total = Bill.objects.filter(
            user=request.user,
            created_at__range=[last_month_start, this_month_start],
            amount__isnull=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Total stats
        total_bills = Bill.objects.filter(user=request.user).count()
        total_spent = Bill.objects.filter(
            user=request.user,
            amount__isnull=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Categorized vs uncategorized
        categorized_count = Bill.objects.filter(
            user=request.user,
            category__isnull=False
        ).count()
        
        uncategorized_count = total_bills - categorized_count
        
        return Response({
            'this_month_total': float(this_month_total),
            'last_month_total': float(last_month_total),
            'total_bills': total_bills,
            'total_spent': float(total_spent),
            'categorized_count': categorized_count,
            'uncategorized_count': uncategorized_count,
            'categorization_percentage': (categorized_count / total_bills * 100) if total_bills > 0 else 0
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all categories"""
        from .models import Category
        categories = Category.objects.all().values('id', 'name', 'type', 'color')
        return Response(list(categories))
    
    @action(detail=False, methods=['post'], parser_classes=[JSONParser])
    def bulk_delete(self, request):
        """Bulk delete bills"""
        bill_ids = request.data.get('bill_ids', [])
        if not bill_ids:
            return Response({'error': 'No bill IDs provided'}, status=400)
        
        deleted_count = 0
        for bill_id in bill_ids:
            try:
                bill = Bill.objects.get(id=bill_id, user=request.user)
                if bill.image:
                    bill.image.delete()
                bill.delete()
                deleted_count += 1
            except Bill.DoesNotExist:
                continue
        
        return Response({'deleted_count': deleted_count})

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
