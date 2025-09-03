import React from "react";
import { AuthenticationHeaderSection } from "./sections/AuthenticationHeaderSection";
import { MainContentSection } from "./sections/MainContentSection";
import { StatusSection } from "./sections/StatusSection";

export const Login = (): JSX.Element => {
  return (
    <div className="min-h-screen flex flex-col bg-[linear-gradient(90deg,rgba(10,10,11,1)_0%,rgba(26,26,27,1)_50%,rgba(17,17,17,1)_100%)]">
      <div className="relative bg-[linear-gradient(90deg,rgba(0,0,0,0)_40%,rgba(255,255,255,0.01)_50%,rgba(0,0,0,0)_60%)]">
        {/* <AuthenticationHeaderSection /> */}

        <div className="px-[79px] pt-[40px]">
          <MainContentSection />
        </div>

        <StatusSection />
      </div>
    </div>
  );
};
