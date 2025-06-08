// This file exports TypeScript types and interfaces used throughout the application.

export interface User {
    id: string;
    username: string;
    email: string;
    role: 'user' | 'admin';
}

export interface Campaign {
    id: string;
    name: string;
    description: string;
    createdAt: string;
    updatedAt: string;
}

export interface FollowUp {
    id: string;
    campaignId: string;
    message: string;
    delayInDays: number;
}

export interface EmailTemplate {
    subject: string;
    body: string;
}

export interface CSVUploadResponse {
    success: boolean;
    message: string;
    importedCount: number;
    failedCount: number;
}