import React, { useState } from 'react';

const FollowUpForm = ({ onSubmit, initialData }) => {
    const [followUpData, setFollowUpData] = useState(initialData || {
        subject: '',
        body: '',
        delay: 0,
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFollowUpData({
            ...followUpData,
            [name]: value,
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(followUpData);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="subject">Subject</label>
                <input
                    type="text"
                    id="subject"
                    name="subject"
                    value={followUpData.subject}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label htmlFor="body">Email Body</label>
                <textarea
                    id="body"
                    name="body"
                    value={followUpData.body}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label htmlFor="delay">Delay (in days)</label>
                <input
                    type="number"
                    id="delay"
                    name="delay"
                    value={followUpData.delay}
                    onChange={handleChange}
                    required
                />
            </div>
            <button type="submit">Save Follow-Up</button>
        </form>
    );
};

export default FollowUpForm;