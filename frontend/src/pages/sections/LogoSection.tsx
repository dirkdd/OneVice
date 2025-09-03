import React from "react";
import { InkReveal, HolographicStagger } from "@/animations/components";
import { FIGMA_ASSETS } from "@/utils/assets";

export const LogoSection = (): JSX.Element => {
  const brandLogos = [
    {
      src: FIGMA_ASSETS.BRAND_LOGO_1,
      alt: "Brand logo 1",
      className: "w-[77px] h-[34px]",
    },
    {
      src: FIGMA_ASSETS.BRAND_LOGO_2,
      alt: "Brand logo 2",
      className: "w-24 h-[27px]",
    },
    {
      src: FIGMA_ASSETS.BRAND_LOGO_3,
      alt: "Brand logo 3",
      className: "w-[87px] h-[34px]",
    },
    {
      src: FIGMA_ASSETS.BRAND_LOGO_4,
      alt: "Brand logo 4",
      className: "w-[92px] h-[34px]",
    },
  ];

  return (
    <div className="flex flex-col items-center space-y-6">
      <div className="relative flex flex-col items-center">
        <div className="relative flex flex-col items-center">
          <div 
            className="flood font-normal text-[120px] tracking-[0] leading-none whitespace-nowrap"
            style={{
              background: 'linear-gradient(90deg, #BC995C 0%, #DBC173 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              textShadow: '0 0 20px rgba(219, 193, 115, 0.4), 0 0 40px rgba(188, 153, 92, 0.2)',
            }}
          >
            ONe
          </div>
          <InkReveal
            revealDirection="center"
            inkColor="#ffffff"
            splatterEffect={true}
            bleedAmount={3}
            className="-mt-4"
          >
            <img
              className="w-[350px] h-28 object-cover"
              alt="VICE logo"
              src={FIGMA_ASSETS.VICE_LOGO}
            />
          </InkReveal>
        </div>
      </div>

      <div className="peridot font-light text-gray-300 text-4xl text-center tracking-[-2.30px] leading-[72px] whitespace-nowrap">
        AI INTELLIGENCE HUB
      </div>

      <HolographicStagger
        staggerDelay={0.15}
        hologramColor="#DBC173"
        glowIntensity={0.8}
        className="mb-12"
      >
        <div className="flex items-center justify-center gap-6 flex-wrap">
          {brandLogos.map((logo, index) => (
            <img
              key={`brand-logo-${index}`}
              className={`${logo.className} object-cover`}
              alt={logo.alt}
              src={logo.src}
            />
          ))}
        </div>
      </HolographicStagger>
    </div>
  );
};
