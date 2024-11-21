import React, { useState } from 'react';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

const API_BASE_URL = 'http://localhost:8000/api';
// Create axios instance with custom config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'multipart/form-data',
  }
});

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [billContext, setBillContext] = useState('');
  const [splitResult, setSplitResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleImageChange = (event) => {
    setSelectedImage(event.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!selectedImage || !billContext) {
      toast.error('Please select an image and provide bill context');
      return;
    }

    const formData = new FormData();
    formData.append('image', selectedImage);
    formData.append('user_bill_context', billContext);

    setIsLoading(true);
    const loadingToast = toast.loading('Processing your bill...');

    try {
      const response = await apiClient.post('/split_bill', formData);

      if (response.data.status === 'ok' && response.data.calculation) {
        setSplitResult(response.data.calculation);
        toast.success('Bill split successfully!');
      } else {
        toast.error('Failed to process the bill');
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = error.code === 'ERR_NETWORK' 
        ? 'Network error: Please check if the server is running'
        : 'An error occurred while processing the bill';
      toast.error(errorMessage);
    } finally {
      toast.dismiss(loadingToast);
      setIsLoading(false);
    }
  };


  return (
    <div className="App">
      <ToastContainer position="top-right" />
      
      <header className="App-header">
        <h1>Splitzie</h1>
      </header>

      <main className="App-main">
        <div className="input-section">
          <div className="input-group">
            <label htmlFor="image-upload" className="input-label">
              Select Bill Image
            </label>
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="file-input"
            />
          </div>

          <div className="input-group">
            <label htmlFor="bill-context" className="input-label">
              Bill Context
            </label>
            <textarea
              id="bill-context"
              value={billContext}
              onChange={(e) => setBillContext(e.target.value)}
              placeholder="Enter bill context..."
              className="text-input"
            />
          </div>

          <button 
            onClick={handleSubmit}
            disabled={isLoading}
            className="submit-button"
          >
            Split Bill
          </button>
        </div>

        {splitResult && (
          <div className="results-section">
            <table className="split-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Amount (₹)</th>
                  <th>Shared Items</th>
                </tr>
              </thead>
              <tbody>
                {splitResult.per_person_split.map((person) => (
                  <tr key={person.name}>
                    <td>{person.name}</td>
                    <td>₹{person.amount.toFixed(2)}</td>
                    <td>
                      <ul className="items-list">
                        {person.shared_items.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="total-amount">
              Total Amount: ₹{splitResult.total_amount.toFixed(2)}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;