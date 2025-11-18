import React, { useState } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'react-toastify';
import './Upload.css';

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [previews, setPreviews] = useState([]);
  const { user } = useAuth();

  // Motivational messages
  const motivationalMessages = [
    "Stay organized, stay ahead! 📊",
    "Every bill uploaded is a step towards better financial management! 💰",
    "Keep track, stay on track! 🎯",
    "Your financial journey starts here! 🚀",
    "Organizing today for a better tomorrow! ✨",
    "Smart people track their expenses! 🧠",
  ];

  const [motivationalMessage] = useState(
    motivationalMessages[Math.floor(Math.random() * motivationalMessages.length)]
  );

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    processFiles(selectedFiles);
  };

  const processFiles = (selectedFiles) => {
    // Validate each file
    const validFiles = [];
    const newPreviews = [];
    
    for (const file of selectedFiles) {
      // Check for duplicates
      const isDuplicate = files.some(existingFile => 
        existingFile.name === file.name && existingFile.size === file.size
      );
      
      if (isDuplicate) {
        toast.warning(`${file.name}: Already added`);
        continue;
      }
      
      // Allow PDFs and images
      const isPdf = file.type === 'application/pdf';
      const isImage = file.type.startsWith('image/');
      if (!isPdf && !isImage) {
        toast.error(`${file.name}: Please upload a PDF or image file`);
        continue;
      }
      // Check if file size is less than 10MB
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`${file.name}: File size should be less than 10MB`);
        continue;
      }
      validFiles.push(file);
      
      // Generate preview
      if (isImage) {
        const reader = new FileReader();
        reader.onload = (e) => {
          newPreviews.push({ name: file.name, url: e.target.result, type: 'image' });
          setPreviews(prev => [...prev, ...newPreviews]);
        };
        reader.readAsDataURL(file);
      } else if (isPdf) {
        newPreviews.push({ name: file.name, url: null, type: 'pdf' });
      }
    }
    
    // Add to existing files instead of replacing
    setFiles(prev => [...prev, ...validFiles]);
    setPreviews(prev => [...prev, ...newPreviews]);
  };

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      processFiles(droppedFiles);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select at least one file');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      let successCount = 0;
      let failCount = 0;

      // Upload files one by one
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        try {
          const formData = new FormData();
          formData.append('image', file);

          console.log('FormData contents:', {
            formDataKeys: Array.from(formData.keys()),
          });

          const response = await api.post('/bills/', formData);

          console.log('Upload response:', response);

          if (response.status === 201) {
            successCount++;
          }
          
          // Update progress
          setUploadProgress(((i + 1) / files.length) * 100);
        } catch (error) {
          console.error(`Upload error for ${file.name}:`, error);
          console.error('Error details:', {
            response: error.response?.data,
            status: error.response?.status,
            message: error.message
          });
          failCount++;
          
          // Handle duplicate bill error
          if (error.response?.data?.error === 'Duplicate bill detected') {
            toast.warning(`${file.name}: ${error.response.data.message}`);
          } else {
            // Handle other errors
            const serverMessage = error.response?.data?.image?.[0] || 
                                 error.response?.data?.message || 
                                 error.response?.data?.detail || 
                                 error.message || 
                                 'Error uploading file';
            toast.error(`${file.name}: ${serverMessage}`);
          }
        }
      }

      // Show summary
      if (successCount > 0) {
        toast.success(`${successCount} bill(s) uploaded and processed successfully`);
      }
      if (failCount > 0) {
        toast.warning(`${failCount} file(s) failed to upload`);
      }

      // Reset files and previews on successful upload
      if (successCount > 0) {
        setFiles([]);
        setPreviews([]);
        setUploadProgress(0);
        document.getElementById('file-upload').value = '';
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Error uploading files');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-left-section">
        <div className="welcome-section">
          <div className="upload-icon-large">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          {user && (
            <h1 className="welcome-title">
              Hey {user.username || user.email?.split('@')[0]}, <br />
              ready to upload <br />
              your bills?
            </h1>
          )}
          <p className="welcome-description">
            Easily upload and manage your bills in one place.
          </p>
          <div className="motivation-box">
            <p className="motivation-text">{motivationalMessage}</p>
          </div>
        </div>
      </div>

      <div className="upload-card">
        <div className="upload-header">
          <h2>Upload Bills</h2>
          <p className="upload-info">We support PDF and image formats up to 10MB</p>
        </div>
        
        <div className="upload-section">
          <div 
            className={`drop-zone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload').click()}
          >
            <input
              type="file"
              id="file-upload"
              accept=".pdf,image/*"
              onChange={handleFileChange}
              className="file-input-hidden"
              disabled={uploading}
              multiple
            />
            <div className="drop-zone-content">
              <svg className="cloud-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"></path>
                <polyline points="8 16 12 12 16 16"></polyline>
                <line x1="12" y1="12" x2="12" y2="21"></line>
              </svg>
              <p className="drop-text">
                {dragActive ? 'Drop your files here!' : 'Drag & drop files here'}
              </p>
              <p className="drop-subtext">or</p>
              <button type="button" className="browse-button">Browse Files</button>
            </div>
          </div>

          {/* Progress Bar */}
          {uploading && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                >
                  <span className="progress-text">{Math.round(uploadProgress)}%</span>
                </div>
              </div>
              <div className="spinner-container">
                <div className="spinner"></div>
                <p>Uploading files...</p>
              </div>
            </div>
          )}

          {/* File Previews */}
          {previews.length > 0 && !uploading && (
            <div className="previews-container">
              <h3>Selected Files ({previews.length})</h3>
              <div className="previews-grid">
                {previews.map((preview, index) => (
                  <div key={index} className="preview-item">
                    {preview.type === 'image' ? (
                      <img src={preview.url} alt={preview.name} className="preview-image" />
                    ) : (
                      <div className="preview-pdf">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                          <polyline points="14 2 14 8 20 8"></polyline>
                          <text x="7" y="17" fontSize="8" fontWeight="bold">PDF</text>
                        </svg>
                      </div>
                    )}
                    <div className="preview-info">
                      <p className="preview-name" title={preview.name}>{preview.name}</p>
                      <p className="preview-size">
                        {(files[index]?.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
            className={`upload-button ${uploading ? 'uploading' : ''}`}
          >
            {uploading ? (
              <>
                <span className="button-spinner"></span>
                Uploading...
              </>
            ) : (
              `Upload ${files.length > 0 ? files.length : ''} Bill${files.length !== 1 ? 's' : ''}`
            )}
          </button>

        </div>
      </div>
    </div>
  );
};

export default Upload;