# Clerk API Integration Fix

## Issue Discovered

From the debug logs, we found that Clerk JWT tokens **do not include user metadata in the token payload itself**:

```
Complete JWT payload keys: ['azp', 'exp', 'fva', 'iat', 'iss', 'nbf', 'sid', 'sts', 'sub', 'v']
Found 0 metadata sources: []
No role found in any metadata sources, using default SALESPERSON
```

The JWT only contains standard claims, not the custom `role`, `department`, and `data_access_level` metadata.

## Root Cause

Clerk stores user metadata (role, department, data_access_level) in the user profile on their servers, not embedded in JWT tokens. This is a security best practice, but it means we need to fetch this data via API.

## Solution Implemented

### Added Clerk API Integration

**Enhanced `_extract_user_data()` method**:
1. Made the method async to support API calls
2. Added fallback to fetch metadata from Clerk API when not found in JWT
3. Added comprehensive error handling and logging

**New `_fetch_user_metadata_from_api()` method**:
1. Makes authenticated request to Clerk API using secret key
2. Fetches user data from `https://api.clerk.dev/v1/users/{user_id}`
3. Extracts metadata from `private_metadata`, `public_metadata`, and `unsafe_metadata`
4. Returns combined metadata with priority (private > public > unsafe)

### Code Changes

```python
# Enhanced extraction with API fallback
async def _extract_user_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # ... existing JWT extraction logic ...
    
    # If no metadata found in JWT, try fetching from Clerk API
    if not role_found and not dept_found and not access_level_found:
        logger.info("No metadata in JWT, attempting to fetch from Clerk API")
        api_metadata = await self._fetch_user_metadata_from_api(user_id)
        if api_metadata:
            if 'role' in api_metadata:
                user_data["role"] = api_metadata['role'].upper()
            # ... extract other fields

# New API integration method
async def _fetch_user_metadata_from_api(self, user_id: str) -> Optional[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {self.clerk_secret_key}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.clerk.dev/v1/users/{user_id}", headers=headers) as response:
            user_data = await response.json()
            # Extract and combine all metadata sources
```

## Expected Results

### With Valid CLERK_SECRET_KEY
```
INFO: No metadata in JWT, attempting to fetch from Clerk API
INFO: Found private_metadata in API response: ['role', 'department', 'data_access_level']
INFO: Role fetched from Clerk API: LEADERSHIP
INFO: Department fetched from Clerk API: executive  
INFO: Data access level fetched from Clerk API: 6
```

### Authentication Flow Now
1. JWT token validated (contains user ID)
2. Metadata extraction attempts multiple JWT formats (finds none)
3. **NEW**: API call to Clerk to fetch user profile metadata
4. Role="LEADERSHIP", department="executive", data_access_level=6 extracted
5. User context created with proper permissions
6. Tools called with correct access level

## Requirements

### Environment Variables
Ensure `CLERK_SECRET_KEY` is set in your environment:
```bash
# In .env or environment
CLERK_SECRET_KEY=sk_live_... # or sk_test_... for development
```

### Dependencies
Added `aiohttp` for async HTTP requests to Clerk API.

## Testing

### 1. Test the API Integration
The debug logs should now show:
```bash
# JWT extraction (will still find 0 metadata sources)
grep "Found 0 metadata sources" logs

# API fallback attempt
grep "attempting to fetch from Clerk API" logs

# Successful API extraction  
grep "Role fetched from Clerk API" logs
grep "LEADERSHIP" logs
```

### 2. Verify Complete Flow
Send the same test query and look for:
- Role should show as "LEADERSHIP" not "SALESPERSON"
- data_sensitivity should be 6 not 1
- Tools should be called (market analysis, lead qualification, etc.)

## Fallback Behavior

If Clerk API call fails:
- Falls back to default values (SALESPERSON, general, 1)
- Logs warning but doesn't break authentication
- System continues to function with basic permissions

## Security Notes

- Uses Clerk secret key for server-to-server authentication
- API calls are made securely with proper headers
- Metadata priority: private_metadata > public_metadata > unsafe_metadata
- No sensitive data logged (only field names, not values)

This fix ensures that even though Clerk doesn't embed metadata in JWT tokens, we can still retrieve the user's role and permissions by making a server-side API call during authentication.