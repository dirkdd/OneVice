import React from "react";
import { LogoSection } from "./LogoSection";
import { XImageSection } from "./XImageSection";
import { SecureAccessSection, AuthenticateCard } from "./SecureAccessSection";

export const MainContentSection = (): JSX.Element => {
  return (
    <section className="w-full max-w-[1200px] mx-auto relative mb-24">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
        
        {/* Left Column - Logo Group + Secure Access */}
        <div className="flex flex-col space-y-48">
          {/* Logo Elements */}
          <LogoSection />
          
          {/* Secure Access Section */}
          <SecureAccessSection />
        </div>

        {/* Right Column - Branded X + Authentication */}
        <div className="flex flex-col space-y-12">
          {/* Branded X */}
          <XImageSection />
          
          {/* Authentication Card */}
          <div className="flex justify-center">
            <AuthenticateCard />
          </div>
        </div>
      </div>
    </section>
  );
};