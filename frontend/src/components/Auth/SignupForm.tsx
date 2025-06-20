import React, { useState } from 'react';
import { useRouter } from 'next/router';

const SignupForm: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }
        setLoading(true);
        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Signup failed');
            }

            setSuccess('Signup successful! Please log in.');
            setEmail('');
            setPassword('');
            setConfirmPassword('');
            setTimeout(() => router.push('/login'), 1500);
        } catch (err: any) {
            setError(err.message || 'Signup failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-md mx-auto mt-12 bg-white shadow-md rounded px-8 py-6">
            <h2 className="text-2xl font-bold mb-6 text-center">Create your Pebble account</h2>
            {error && <p className="text-red-600 mb-4 text-center">{error}</p>}
            {success && <p className="text-green-600 mb-4 text-center">{success}</p>}
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
                    autoComplete="new-password"
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
            <div className="mb-4 relative">
                <label htmlFor="confirmPassword" className="block text-gray-700 font-medium mb-1">Confirm Password</label>
                <input
                    type={showConfirm ? 'text' : 'password'}
                    id="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoComplete="new-password"
                />
                <button
                    type="button"
                    className="absolute right-2 top-8 text-sm text-gray-500 hover:text-gray-700 focus:outline-none"
                    onClick={() => setShowConfirm((v) => !v)}
                    tabIndex={-1}
                >
                    {showConfirm ? 'Hide' : 'Show'}
                </button>
            </div>
            <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition"
            >
                {loading ? 'Signing up...' : 'Sign Up'}
            </button>
            <div className="mt-4 text-center text-sm text-gray-500">
                Already have an account? <a href="/login" className="text-blue-600 hover:underline">Login</a>
            </div>
        </form>
    );
};

export default SignupForm;