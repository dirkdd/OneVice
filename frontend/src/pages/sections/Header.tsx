import React from "react";
import { Button } from "@/components/ui/button";
import { Bell } from "lucide-react";

export const Header = (): JSX.Element => {
  return (
    <div className="bg-[#0a0a0b] border-b border-gray-800 p-6">
      <div className="flex items-center justify-between">
        {/* Logo Section */}
        <div className="flex items-center">
          <div className="flex flex-col items-center">
            <div className="flood text-3xl bg-[linear-gradient(90deg,rgba(188,153,92,1)_0%,rgba(219,193,115,1)_100%)] [-webkit-background-clip:text] bg-clip-text [-webkit-text-fill-color:transparent] [text-fill-color:transparent] leading-none">
              One
            </div>
            <img 
              src="/figmaAssets/image-1.png"
              alt="VICE Logo" 
              className="h-8 object-contain -mt-1"
            />
          </div>
        </div>
        
        {/* Navigation Links - Centered */}
        <nav className="flex gap-8">
          <a href="#" className="text-white font-medium">Platform</a>
          <a href="#" className="text-gray-400 hover:text-white">Intelligence</a>
          <a href="#" className="text-gray-400 hover:text-white">Analytics</a>
          <a href="#" className="text-gray-400 hover:text-white">Security</a>
        </nav>
        
        {/* Right Section */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon">
            <Bell className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-400">System Online</span>
          </div>
        </div>
      </div>
    </div>
  );
};