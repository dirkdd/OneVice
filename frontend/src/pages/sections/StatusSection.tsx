import React from "react";
import { Button } from "@/components/ui/button";
import { FIGMA_ASSETS } from "@/utils/assets";

export const StatusSection = (): JSX.Element => {
  const statusItems = [
    {
      label: "AI Engine:",
      status: "ONLINE",
      color: "bg-[#dfff00]",
      textColor: "text-[#dfff00]",
    },
    {
      label: "Security:",
      status: "SECURE",
      color: "bg-[#dfff00]",
      textColor: "text-[#dfff00]",
    },
    {
      label: "Data Sync:",
      status: "LIVE",
      color: "bg-[#0099ff]",
      textColor: "text-[#0099ff]",
    },
  ];

  return (
    <section className="w-full h-[46px] bg-[#1e1e1ea6] border border-solid border-[#ffffff1a]">
      <div className="flex items-center justify-between w-full max-w-[1280px] mx-auto px-6 h-full">
        <div className="flex items-center gap-5">
          {statusItems.map((item, index) => (
            <div key={index} className="flex items-center gap-4">
              <div
                className={`w-2 h-2 ${item.color} rounded-full opacity-95`}
              />
              <div className="peridot font-normal text-sm">
                <span className="text-gray-300">{item.label}</span>
                <span className={`font-medium ${item.textColor}`}>&nbsp;</span>
                <span className="font-medium text-white">{item.status}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-400 peridot">
          <span className="whitespace-nowrap">Last Update: 2 min ago</span>
          <span>|</span>
          <span className="whitespace-nowrap">Version 2.1.0</span>
          <Button variant="ghost" size="sm" className="h-auto p-1">
            <img
              className="w-3 h-4"
              alt="Button"
              src={FIGMA_ASSETS.BUTTONS.SECONDARY}
            />
          </Button>
        </div>
      </div>
    </section>
  );
};
