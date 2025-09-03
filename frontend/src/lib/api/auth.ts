// Legacy auth API - now deprecated since we use Clerk
// Keeping only the types and essential interfaces for backward compatibility

export class AuthApi {
  // All methods are no-ops since Clerk handles authentication
  
  async updatePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    throw new Error('Password management is handled by Clerk. Use Clerk Dashboard for password policies.');
  }

  async requestPasswordReset(email: string): Promise<{ message: string }> {
    throw new Error('Password reset is handled by Clerk authentication flow.');
  }

  async verifyEmail(token: string): Promise<{ message: string }> {
    throw new Error('Email verification is handled by Clerk authentication flow.');
  }

  // Legacy methods kept for compatibility
  isAuthenticated(): boolean {
    console.warn('authApi.isAuthenticated() is deprecated. Use Clerk useUser hook instead.');
    return false;
  }

  getToken(): string | null {
    console.warn('authApi.getToken() is deprecated. Use Clerk useAuth getToken instead.');
    return null;
  }
}

// Export singleton instance for backward compatibility
export const authApi = new AuthApi();
export default authApi;