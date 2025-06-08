import React from 'react';
import Link from 'next/link';

const Home: React.FC = () => {
    return (
        <div>
            <h1>Welcome to the AI-Powered Outreach Application</h1>
            <p>
                This application allows you to manage your email outreach campaigns effectively using AI.
            </p>
            <nav>
                <ul>
                    <li>
                        <Link href="/login">Login</Link>
                    </li>
                    <li>
                        <Link href="/signup">Sign Up</Link>
                    </li>
                    <li>
                        <Link href="/campaigns">Manage Campaigns</Link>
                    </li>
                    <li>
                        <Link href="/email-generation">Generate Emails</Link>
                    </li>
                    <li>
                        <Link href="/follow-ups">Manage Follow-Ups</Link>
                    </li>
                </ul>
            </nav>
        </div>
    );
};

export default Home;