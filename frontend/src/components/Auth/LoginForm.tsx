import React, { useState } from 'react';
import { useRouter } from 'next/router';

const LoginForm: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Login failed. Please check your credentials.');
            }

            const data = await response.json();
            // Store token and redirect to dashboard or campaigns
            localStorage.setItem('token', data.access_token);
            router.push('/campaigns');
        } catch (err: any) {
            setError(err.message || 'Login failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-md mx-auto mt-12 bg-white shadow-md rounded px-8 py-6">
            <h2 className="text-2xl font-bold mb-6 text-center">Sign in to Pebble</h2>
            {error && <p className="text-red-600 mb-4 text-center">{error}</p>}
            <div className="mb-4">
                <label htmlFor="email" className="block text-gray-700 font-medium mb-1">Email</label>
                <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoComplete="email"
                />
            </div>
            <div className="mb-4 relative">
                <label htmlFor="password" className="block text-gray-700 font-medium mb-1">Password</label>
                <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoComplete="current-password"
                />
                <button
                    type="button"
                    className="absolute right-2 top-8 text-sm text-gray-500 hover:text-gray-700 focus:outline-none"
                    onClick={() => setShowPassword((v) => !v)}
                    tabIndex={-1}
                >
                    {showPassword ? 'Hide' : 'Show'}
                </button>
            </div>
            <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition"
            >
                {loading ? 'Logging in...' : 'Login'}
            </button>
            <div className="mt-4 text-center text-sm text-gray-500">
                Don&apos;t have an account? <a href="/signup" className="text-blue-600 hover:underline">Sign up</a>
            </div>
        </form>
    );
};

export default LoginForm;