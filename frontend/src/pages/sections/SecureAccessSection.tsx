import { EyeIcon } from "lucide-react";
import React, { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { useSignIn, useUser } from "@clerk/clerk-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FIGMA_ASSETS } from "@/utils/assets";

const securityFeatures = [
  {
    icon: FIGMA_ASSETS.SECURITY_ICONS.ENTERPRISE,
    title: "Enterprise Security",
    description: "Role-based access control",
  },
  {
    icon: FIGMA_ASSETS.SECURITY_ICONS.ENCRYPTION,
    title: "Encrypted Authentication",
    description: "Multi-factor verification",
  },
  {
    icon: FIGMA_ASSETS.SECURITY_ICONS.SESSION,
    title: "Session Management",
    description: "Automatic timeout protection",
  },
];

// SecureAccessSection component - Left column content
export const SecureAccessSection = (): JSX.Element => {
  return (
    <div className="flex flex-col max-w-md">
      <div className="mb-8">
        <h1 className="text-5xl font-black text-white tracking-[-0.82px] leading-[48px] mb-8">
          SECURE<span className="text-[#ff00ff]">&nbsp;</span>ACCESS
        </h1>

        <p className="text-lg text-gray-300 leading-7">
          Enter the One Vice AI Intelligence Hub. Your gateway to
          conversational business intelligence.
        </p>
      </div>

      <div className="space-y-4">
        {securityFeatures.map((feature, index) => (
          <Card key={index} className="rounded-3xl border-[#ffffff1a] bg-[linear-gradient(90deg,rgba(26,26,27,0.95)_0%,rgba(17,17,17,0.98)_100%)]">
            <CardContent className="flex items-center gap-4 p-4">
              <img 
                src={feature.icon} 
                alt="" 
                className="w-8 h-8" 
              />
              <div>
                <div className="text-white text-sm font-normal leading-5">
                  {feature.title}
                </div>
                <div className="text-gray-400 text-xs font-normal leading-4">
                  {feature.description}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

// AuthenticateCard component - Right column content
export const AuthenticateCard = (): JSX.Element => {
  const [, setLocation] = useLocation();
  const { signIn, setActive, isLoaded } = useSignIn();
  const { isSignedIn, isLoaded: userLoaded } = useUser();
  
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    remember_me: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);

  // Check if user is already signed in and redirect
  useEffect(() => {
    if (userLoaded && isSignedIn && !isRedirecting) {
      console.log('User already signed in, redirecting to dashboard');
      setIsRedirecting(true);
      setLocation('/dashboard');
    }
  }, [isSignedIn, userLoaded, setLocation, isRedirecting]);

  // Show loading state while checking authentication
  if (!userLoaded) {
    return (
      <div className="flex flex-col max-w-md lg:max-w-lg">
        <Card className="rounded-3xl border-[#ffffff1a] bg-[linear-gradient(90deg,rgba(26,26,27,0.95)_0%,rgba(17,17,17,0.98)_100%)] p-8">
          <CardContent className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-gray-400">Checking authentication...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show redirecting state
  if (isRedirecting) {
    return (
      <div className="flex flex-col max-w-md lg:max-w-lg">
        <Card className="rounded-3xl border-[#ffffff1a] bg-[linear-gradient(90deg,rgba(26,26,27,0.95)_0%,rgba(17,17,17,0.98)_100%)] p-8">
          <CardContent className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-gray-400">Redirecting to dashboard...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear errors when user starts typing
    if (localError) setLocalError(null);
  };

  const validateForm = () => {
    if (!formData.email.trim()) {
      setLocalError("Email is required");
      return false;
    }
    if (!formData.email.includes("@")) {
      setLocalError("Please enter a valid email address");
      return false;
    }
    if (!formData.password.trim()) {
      setLocalError("Password is required");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevent submission if already signed in
    if (isSignedIn) {
      setLocalError('You are already signed in. Redirecting...');
      setIsRedirecting(true);
      setLocation('/dashboard');
      return;
    }
    
    if (!validateForm()) return;
    if (!isLoaded) return;

    setIsLoading(true);
    setLocalError(null);

    try {
      const result = await signIn.create({
        identifier: formData.email.trim(),
        password: formData.password,
      });

      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId });
        console.log('Login successful, redirecting to dashboard');
        // Set redirecting state and navigate
        setIsRedirecting(true);
        setLocation('/dashboard');
      } else {
        // Handle additional verification steps if needed
        console.log('Additional verification required:', result.status);
        setLocalError('Additional verification required');
      }
    } catch (err: any) {
      console.error('Login failed:', err);
      const errorMessage = err.errors?.[0]?.message || 'Authentication failed. Please check your credentials.';
      setLocalError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const displayError = localError;

  return (
    <div className="flex flex-col max-w-md lg:max-w-lg">
      <Card className="rounded-3xl border-[#ffffff1a] bg-[linear-gradient(90deg,rgba(26,26,27,0.95)_0%,rgba(17,17,17,0.98)_100%)] p-8">
        <CardContent className="space-y-8 p-0">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-2">
              AUTHENTICATE
            </h2>
            <p className="text-sm text-gray-400">
              Access your intelligence dashboard
            </p>
          </div>

          {displayError && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
              <p className="text-red-400 text-sm">{displayError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label
                htmlFor="email"
                className="text-sm text-gray-300 font-normal"
              >
                EMAIL ADDRESS
              </Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="your.email@company.com"
                className="h-[58px] bg-[#111111cc] border-[#ffffff1a] rounded-xl text-white text-base placeholder:text-[#adaebc]"
                disabled={isLoading}
                autoComplete="email"
                required
              />
            </div>

            <div className="space-y-2">
              <Label
                htmlFor="password"
                className="text-sm text-gray-300 font-normal"
              >
                PASSWORD
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  placeholder="Enter your password"
                  className="h-[58px] bg-[#111111cc] border-[#ffffff1a] rounded-xl text-white text-base pr-12 placeholder:text-[#adaebc]"
                  disabled={isLoading}
                  autoComplete="current-password"
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 h-auto p-0 hover:bg-transparent"
                  disabled={isLoading}
                >
                  <EyeIcon className={`w-4 h-4 ${showPassword ? 'text-white' : 'text-gray-400'}`} />
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={formData.remember_me}
                  onCheckedChange={(checked) => 
                    handleInputChange('remember_me', !!checked)
                  }
                  className="bg-white border-black rounded-[1px] data-[state=checked]:bg-white data-[state=checked]:text-black"
                  disabled={isLoading}
                />
                <Label
                  htmlFor="remember"
                  className="text-sm text-gray-300 font-normal"
                >
                  Remember device
                </Label>
              </div>
              <Button
                type="button"
                variant="link"
                className="text-sm text-white font-medium p-0 h-auto hover:text-gray-300"
                disabled={isLoading}
              >
                Forgot password?
              </Button>
            </div>

            <Button 
              type="submit"
              disabled={isLoading || isRedirecting}
              className="w-full h-[60px] bg-white text-[#0a0a0b] font-bold text-lg rounded-xl shadow-[0px_0px_20px_#ffffff4c,0px_0px_40px_#ffffff1a] hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "AUTHENTICATING..." : isRedirecting ? "REDIRECTING..." : "ACCESS HUB"}
              {!isLoading && !isRedirecting && (
                <img
                  src={FIGMA_ASSETS.UI_ELEMENTS.ICON_2}
                  alt=""
                  className="w-4 h-[21px] ml-2"
                />
              )}
            </Button>
          </form>

          <div className="border-t border-[#ffffff1a] pt-6">
            <div className="text-center mb-4">
              <p className="text-sm text-gray-400">Alternative Access</p>
            </div>

            <div className="flex gap-3">
              <Card className="flex-1 bg-[#1e1e1ea6] border-[#ffffff1a] rounded-lg">
                <CardContent className="flex items-center justify-center p-3">
                  <img
                    src={FIGMA_ASSETS.UI_ELEMENTS.ALTERNATIVE_LOGIN}
                    alt="Alternative login"
                    className="w-[61px] h-5 object-cover brightness-0 invert"
                  />
                </CardContent>
              </Card>

              <Card className="flex-1 bg-[#1e1e1ea6] border-[#ffffff1a] rounded-lg">
                <CardContent className="flex items-center justify-center gap-2 p-3">
                  <img
                    src={FIGMA_ASSETS.UI_ELEMENTS.ICON_1}
                    alt=""
                    className="w-4 h-6"
                  />
                  <span className="text-sm text-white font-medium">
                    Biometric
                  </span>
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="text-center text-xs">
            <span className="text-gray-500">
              Need access? Contact your administrator or{" "}
            </span>
            <Button
              variant="link"
              className="text-white font-medium p-0 h-auto text-xs hover:text-gray-300"
            >
              request access
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
