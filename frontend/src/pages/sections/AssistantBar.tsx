import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { User, Download, Share, MoreHorizontal } from "lucide-react";
import { DashboardContext } from "../Dashboard";

interface AssistantBarProps {
  context: DashboardContext;
}

export const AssistantBar = ({ context }: AssistantBarProps): JSX.Element => {
  return (
    <div className="bg-[#0a0a0b] border-b border-gray-800 p-6">
      <div className="flex items-center justify-between">
        {/* Assistant Identity */}
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <User className="w-4 h-4" />
          <span>One Vice AI Leadership Assistant</span>
          <Badge variant="secondary" className="bg-green-500/20 text-green-400">Leadership Intelligence • Full Access</Badge>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center gap-4">
          {context !== "home" && (
            <>
              <Button variant="ghost" size="icon">
                <Download className="w-5 h-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <Share className="w-5 h-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="w-5 h-5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};