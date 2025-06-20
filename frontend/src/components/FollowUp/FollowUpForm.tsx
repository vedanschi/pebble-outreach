import React, { useState } from 'react';

interface FollowUpFormProps {
    campaignId: number;
    onSubmit: (data: FollowUpData) => void;
    initialData?: FollowUpData;
}

interface FollowUpData {
    subject: string;
    body: string;
    delay: number;
}

const FollowUpForm: React.FC<FollowUpFormProps> = ({ campaignId, onSubmit, initialData }) => {
    const [followUpData, setFollowUpData] = useState<FollowUpData>(
        initialData || {
            subject: '',
            body: '',
            delay: 0,
        }
    );
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFollowUpData((prev) => ({
            ...prev,
            [name]: name === 'delay' ? Number(value) : value,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            await onSubmit({ ...followUpData });
        } catch (err: any) {
            setError(err?.message || 'Failed to save follow-up');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4 bg-purple-50 p-4 rounded border border-purple-200">
            <div>
                <label htmlFor="subject" className="block font-medium mb-1">Subject</label>
                <input
                    type="text"
                    id="subject"
                    name="subject"
                    value={followUpData.subject}
                    onChange={handleChange}
                    required
                    className="w-full border rounded px-2 py-1"
                />
            </div>
            <div>
                <label htmlFor="body" className="block font-medium mb-1">Email Body</label>
                <textarea
                    id="body"
                    name="body"
                    value={followUpData.body}
                    onChange={handleChange}
                    required
                    className="w-full border rounded px-2 py-1"
                    rows={4}
                />
            </div>
            <div>
                <label htmlFor="delay" className="block font-medium mb-1">Delay (in days)</label>
                <input
                    type="number"
                    id="delay"
                    name="delay"
                    value={followUpData.delay}
                    onChange={handleChange}
                    required
                    min={0}
                    className="w-full border rounded px-2 py-1"
                />
            </div>
            {error && <div className="text-red-500 text-sm">{error}</div>}
            <button
                type="submit"
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
                disabled={submitting}
            >
                {submitting ? 'Saving...' : 'Save Follow-Up'}
            </button>
        </form>
    );
};

export default FollowUpForm;