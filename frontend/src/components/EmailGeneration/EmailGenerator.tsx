import React, { useState } from 'react';

const EmailGenerator: React.FC = () => {
    const [prompt, setPrompt] = useState('');
    const [generatedEmail, setGeneratedEmail] = useState('');

    const handleGenerateEmail = async () => {
        try {
            const response = await fetch('/api/generate-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (!response.ok) {
                throw new Error('Failed to generate email');
            }

            const data = await response.json();
            setGeneratedEmail(data.email);
        } catch (error) {
            console.error(error);
            alert('Error generating email. Please try again.');
        }
    };

    return (
        <div>
            <h1>Email Generator</h1>
            <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your email prompt here..."
                rows={5}
                cols={50}
            />
            <button onClick={handleGenerateEmail}>Generate Email</button>
            {generatedEmail && (
                <div>
                    <h2>Generated Email:</h2>
                    <pre>{generatedEmail}</pre>
                </div>
            )}
        </div>
    );
};

export default EmailGenerator;