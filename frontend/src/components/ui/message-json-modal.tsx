import React, { useState } from "react";
import { X, Copy, Check } from "lucide-react";
import { WebSocketMessage } from "@/lib/api/types";
import { MessageWithAgent } from "@/types/conversation-history";
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose 
} from "./dialog";
import { Button } from "./button";
import { cn } from "@/lib/utils";

interface MessageJSONModalProps {
  message: WebSocketMessage | MessageWithAgent;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  className?: string;
}

export const MessageJSONModal: React.FC<MessageJSONModalProps> = ({
  message,
  open,
  onOpenChange,
  className
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Format JSON with syntax highlighting
  const formatJSON = (obj: any): string => {
    return JSON.stringify(obj, null, 2);
  };

  // Copy to clipboard functionality
  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // Separate content and full message JSON
  const contentOnly = message.content;
  const fullMessage = formatJSON(message);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className={cn(
          "max-w-4xl max-h-[80vh]",
          className
        )}
      >
        <DialogHeader className="space-y-3">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-semibold">
              Message Data
            </DialogTitle>
            <DialogClose asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </DialogClose>
          </div>
          
          <div className="flex items-center gap-2 text-sm opacity-80">
            <span className="px-2 py-1 bg-gray-800/60 rounded text-xs">
              {(message as WebSocketMessage).type || 'message'}
            </span>
            {(message as WebSocketMessage).timestamp && (
              <span className="text-xs">
                {new Date((message as WebSocketMessage).timestamp).toLocaleString()}
              </span>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-6 overflow-hidden">
          {/* Message Content Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Content</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(contentOnly, 'content')}
                className="h-8 px-3 hover:bg-gray-700/50 opacity-80 hover:opacity-100"
              >
                {copiedField === 'content' ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </>
                )}
              </Button>
            </div>
            
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-4 max-h-60 overflow-y-auto">
              <pre className="text-sm opacity-90 whitespace-pre-wrap break-words font-mono leading-relaxed">
                {contentOnly}
              </pre>
            </div>
          </div>

          {/* Full JSON Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Full Message JSON</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(fullMessage, 'full')}
                className="h-8 px-3 hover:bg-gray-700/50 opacity-80 hover:opacity-100"
              >
                {copiedField === 'full' ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    Copy JSON
                  </>
                )}
              </Button>
            </div>
            
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-4 max-h-80 overflow-auto">
              <pre className="text-xs opacity-80 font-mono leading-relaxed">
                {fullMessage}
              </pre>
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-gray-700/30">
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            className="hover:bg-gray-700/50 opacity-80 hover:opacity-100"
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};