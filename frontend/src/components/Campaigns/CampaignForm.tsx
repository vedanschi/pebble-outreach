import React, { useState } from 'react';
import type { Campaign } from '../../types';

interface CampaignFormProps {
    initialData?: Partial<Campaign>;
    onSubmit: (data: { name: string; description: string }) => Promise<void>;
}

const CampaignForm: React.FC<CampaignFormProps> = ({ initialData, onSubmit }) => {
    const [name, setName] = useState(initialData?.name || '');
    const [description, setDescription] = useState(initialData?.description || '');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
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
        <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded shadow max-w-lg mx-auto">
            <div>
                <label htmlFor="name" className="block font-medium mb-1">Campaign Name</label>
                <input
                    type="text"
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full border rounded px-2 py-1"
                />
            </div>
            <div>
                <label htmlFor="description" className="block font-medium mb-1">Description</label>
                <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                    className="w-full border rounded px-2 py-1"
                    rows={3}
                />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
                type="submit"
                disabled={isSubmitting}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
                {isSubmitting ? 'Saving...' : 'Save Campaign'}
            </button>
        </form>
    );
};

export default CampaignForm;