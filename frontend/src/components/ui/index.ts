// Agent Selection System
export { AgentSelector } from './agent-selector';
export { AgentSettingsPanel, AgentSettingsButton } from './agent-settings-panel';
export { AgentBadge, SalesAgentBadge, TalentAgentBadge, AnalyticsAgentBadge, getAgentColorScheme } from './agent-badge';
export { AgentMessage, SalesMessage, TalentMessage, AnalyticsMessage } from './agent-message';
export { AgentProcessingIndicator } from './agent-processing-indicator';

// Specialized Agent Components - Rich domain-specific UI components
export * from './agent-components';

// Re-export shadcn/ui components for convenience
export { Button } from './button';
export { Input } from './input';
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
export { Badge } from './badge';
export { Switch } from './switch';
export { Label } from './label';
export { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from './sheet';
export { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
export { Separator } from './separator';
export { Skeleton } from './skeleton';
export { Avatar, AvatarFallback, AvatarImage } from './avatar';
export { Progress } from './progress';
export { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './alert-dialog';
export { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './dialog';
export { Popover, PopoverContent, PopoverTrigger } from './popover';
export { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip';

// Types
export type { RoutingMode, AgentPreferences } from './agent-selector';