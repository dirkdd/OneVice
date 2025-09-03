import React from "react";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";

export const AuthenticationHeaderSection = (): JSX.Element => {
  const navigationItems = [
    { label: "Platform", href: "#" },
    { label: "Intelligence", href: "#" },
    { label: "Analytics", href: "#" },
    { label: "Security", href: "#" },
  ];

  return (
    <header className="w-full h-[78px] bg-[#1e1e1ea6] border border-solid border-[#ffffff1a]">
      <div className="relative w-full max-w-[1280px] h-[76px] mx-auto px-20">
        <div className="relative w-full h-11 top-4 px-6">
          <div className="flex justify-center items-center h-full">
            <NavigationMenu>
              <NavigationMenuList className="flex gap-8">
                {navigationItems.map((item, index) => (
                  <NavigationMenuItem key={index}>
                    <NavigationMenuLink
                      href={item.href}
                      className="peridot font-medium text-gray-300 text-sm tracking-[0] leading-5 whitespace-nowrap hover:text-white transition-colors"
                    >
                      {item.label}
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                ))}
              </NavigationMenuList>
            </NavigationMenu>
          </div>

          <div className="absolute w-[156px] h-[42px] top-px right-0 flex items-center">
            <img
              className="w-[34px] h-[42px]"
              alt="Button"
              src="/figmaAssets/button.svg"
            />

            <div className="w-2 h-2 ml-4 bg-[#dfff00] rounded-full opacity-50" />

            <div className="ml-6 peridot font-normal text-gray-400 text-xs tracking-[0] leading-4 whitespace-nowrap">
              System Online
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
