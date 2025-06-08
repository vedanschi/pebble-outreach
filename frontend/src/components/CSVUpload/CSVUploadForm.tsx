import React, { useState } from 'react';

const CSVUploadForm: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile && selectedFile.type === 'text/csv') {
            setFile(selectedFile);
            setError(null);
        } else {
            setError('Please upload a valid CSV file.');
            setFile(null);
        }
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!file) {
            setError('Please select a file before submitting.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload-csv', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to upload CSV file.');
            }

            setSuccess('CSV file uploaded successfully!');
            setFile(null);
        } catch (error) {
            setError(error.message);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h2>Upload CSV File</h2>
            <input type="file" accept=".csv" onChange={handleFileChange} />
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {success && <p style={{ color: 'green' }}>{success}</p>}
            <button type="submit">Upload</button>
        </form>
    );
};

export default CSVUploadForm;