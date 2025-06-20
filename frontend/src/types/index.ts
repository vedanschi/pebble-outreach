// This file exports TypeScript types and interfaces used throughout the application.

export interface User {
    id: string;
    username: string;
    email: string;
    role: 'user' | 'admin';
    isActive?: boolean;
    companyName?: string;
    smtpConfig?: SMTPConfig;
}

export interface SMTPConfig {
    host: string;
    port: number;
    username: string;
    senderEmail: string;
    useTLS: boolean;
}

export interface Campaign {
    id: string;
    name: string;
    description: string;
    status: 'draft' | 'active' | 'completed' | 'paused' | 'sending';
    createdAt: string;
    updatedAt: string;
    emailsSent?: SentEmail[];
    contacts?: Contact[];
    contactsCount?: number;
    opensCount?: number;
    // Add any other backend-provided stats here
}

export interface SentEmail {
    id: string;
    subject: string;
    body: string;
    status: string;
    sentAt: string;
    openedAt?: string;
    clickedAt?: string;
    contactId: string;
    trackingPixelId?: string;
    recipient?: string; // for UI compatibility
    to?: string; // for UI compatibility
    opensCount?: number; // for UI compatibility
    opens?: number; // for UI compatibility
    // Add any other backend-provided fields here
}

export interface Contact {
    id: string;
    campaignId: string;
    firstName: string;
    lastName: string;
    email: string;
    companyName: string;
    [key: string]: any; // For custom fields
}

export interface FollowUp {
    id: string;
    campaignId: string;
    message: string;
    delayInDays: number;
    status?: string;
    scheduledAt?: string;
}

export interface EmailTemplate {
    subject: string;
    body: string;
    isFollowUp?: boolean;
}

export interface CSVUploadResponse {
    success: boolean;
    message: string;
    importedCount: number;
    failedCount: number;
    errors?: string[];
}