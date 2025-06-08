import React, { useState } from 'react';

const CampaignForm = ({ initialData, onSubmit }) => {
    const [title, setTitle] = useState(initialData ? initialData.title : '');
    const [description, setDescription] = useState(initialData ? initialData.description : '');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);

        try {
            await onSubmit({ title, description });
        } catch (err) {
            setError('Failed to save campaign. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="title">Campaign Title</label>
                <input
                    type="text"
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                />
            </div>
            <div>
                <label htmlFor="description">Description</label>
                <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                />
            </div>
            {error && <p className="error">{error}</p>}
            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save Campaign'}
            </button>
        </form>
    );
};

export default CampaignForm;