import React, { useState } from 'react';

interface CSVUploadFormProps {
  campaignId: number;
}

const CSVUploadForm: React.FC<CSVUploadFormProps> = ({ campaignId }) => {
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (!selectedFile) {
            setFile(null);
            setError('No file selected.');
            return;
        }
        if (!selectedFile.name.endsWith('.csv')) {
            setError('Please upload a valid CSV file.');
            setFile(null);
            return;
        }
        setFile(selectedFile);
        setError(null);
        setSuccess(null);
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError(null);
        setSuccess(null);
        if (!file) {
            setError('Please select a file before submitting.');
            return;
        }
        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/api/upload-csv', {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.message || 'Failed to upload CSV file.');
            }
            setSuccess('CSV file uploaded successfully!');
            setFile(null);
        } catch (error: any) {
            setError(error.message || 'Failed to upload CSV file.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-md mx-auto mt-8 bg-white shadow-md rounded px-8 py-6">
            <h2 className="text-xl font-bold mb-4 text-purple-700">Upload Contacts CSV</h2>
            <div className="mb-4">
                <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
                />
            </div>
            {error && <p className="text-red-600 mb-2">{error}</p>}
            {success && <p className="text-green-600 mb-2">{success}</p>}
            <button
                type="submit"
                disabled={uploading || !file}
                className="w-full bg-gradient-to-r from-purple-400 to-purple-700 text-white py-2 rounded font-semibold hover:from-purple-500 hover:to-purple-800 transition"
            >
                {uploading ? 'Uploading...' : 'Upload CSV'}
            </button>
        </form>
    );
};

export default CSVUploadForm;