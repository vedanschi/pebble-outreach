import React, { useState } from 'react';

interface CampaignFormProps {
    initialData?: {
        name: string;
        description: string;
    };
    onSubmit: (data: { name: string; description: string }) => Promise<void>;
}

const CampaignForm: React.FC<CampaignFormProps> = ({ initialData, onSubmit }) => {
    const [name, setName] = useState(initialData ? initialData.name : '');
    const [description, setDescription] = useState(initialData ? initialData.description : '');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);

        try {
            await onSubmit({ name, description });
        } catch (err) {
            setError('Failed to save campaign. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="bg-white rounded shadow p-6 mb-4">
            <div className="mb-4">
                <label htmlFor="name" className="block font-medium mb-1">Campaign Name</label>
                <input
                    type="text"
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full border px-3 py-2 rounded"
                />
            </div>
            <div className="mb-4">
                <label htmlFor="description" className="block font-medium mb-1">Description</label>
                <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                    className="w-full border px-3 py-2 rounded"
                />
            </div>
            {error && <p className="text-red-600 mb-2">{error}</p>}
            <button
                type="submit"
                disabled={isSubmitting}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
                {isSubmitting ? 'Saving...' : 'Save Campaign'}
            </button>
        </form>
    );
};

export default CampaignForm;