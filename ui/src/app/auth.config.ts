import { AuthConfig } from 'angular-oauth2-oidc';

export const authConfig: AuthConfig = {
  issuer: '{AUTHENTIK_JWT_ISSUER}',
  redirectUri: window.location.origin,
  clientId: '{AUTHENTIK_CLIENT_ID}',
  showDebugInformation: true,
  requireHttps: false,
  strictDiscoveryDocumentValidation: false,
};
