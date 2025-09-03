import React from "react";
import { GlitchEffect } from "@/animations/components";

export const XImageSection = (): JSX.Element => {
  return (
    <div className="flex items-center justify-center">
      <GlitchEffect
        glitchIntensity={1.2}
        colorShift={true}
        scanLines={true}
        distortionAmount={3}
        className="cursor-pointer"
      >
        <img 
          src="/figmaAssets/x-branded.png"
          alt="Branded X"
          className="w-[200px] md:w-[250px] lg:w-[296px] object-contain"
        />
      </GlitchEffect>
    </div>
  );
};