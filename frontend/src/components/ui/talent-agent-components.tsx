import React from "react";
import { cn } from "@/lib/utils";
import { Card } from "./card";
import { Badge } from "./badge";
import { Button } from "./button";
import { Avatar, AvatarFallback, AvatarImage } from "./avatar";
import { 
  MetricCard, 
  ProgressBar, 
  StatusIndicator, 
  DataList, 
  QuickStats 
} from "./agent-visualizations";
import {
  User,
  Users,
  Star,
  Calendar,
  Clock,
  MapPin,
  Award,
  Briefcase,
  Phone,
  Mail,
  ExternalLink,
  Camera,
  Film,
  Mic,
  Edit,
  Play,
  Headphones,
  Palette,
  Code,
  Shield,
  CheckCircle,
  AlertCircle,
  XCircle,
  Filter,
  Search,
  BookOpen,
  TrendingUp,
  Activity
} from "lucide-react";

// Talent-specific Types
export interface CrewMemberProfile {
  id: string;
  name: string;
  avatar?: string;
  title: string;
  bio?: string;
  experience_years: number;
  location: string;
  skills: TalentSkill[];
  availability: AvailabilityStatus;
  rate: RateInfo;
  performance_score: number;
  projects_completed: number;
  specialties: string[];
  contact: {
    email?: string;
    phone?: string;
    website?: string;
  };
  portfolio: PortfolioItem[];
  reviews?: Review[];
  union_status?: UnionInfo;
}

export interface TalentSkill {
  id: string;
  name: string;
  category: 'technical' | 'creative' | 'leadership' | 'communication';
  proficiency: number; // 1-10
  years_experience: number;
  certifications?: string[];
  last_used?: string;
}

export interface AvailabilityStatus {
  status: 'available' | 'booked' | 'limited' | 'unavailable';
  next_available?: string;
  calendar_url?: string;
  notes?: string;
  hourly_capacity?: number;
}

export interface RateInfo {
  min: number;
  max: number;
  currency: string;
  per: 'hour' | 'day' | 'week' | 'project' | 'episode';
  negotiable: boolean;
}

export interface PortfolioItem {
  id: string;
  title: string;
  type: 'video' | 'image' | 'audio' | 'document';
  thumbnail?: string;
  url?: string;
  description?: string;
  role?: string;
  year?: number;
  awards?: string[];
}

export interface Review {
  id: string;
  reviewer: string;
  rating: number;
  comment: string;
  project?: string;
  date: string;
}

export interface UnionInfo {
  unions: string[];
  member_since?: string;
  status: 'active' | 'inactive' | 'pending';
}

export interface RoleMatchingData {
  role: string;
  requirements: string[];
  candidates: Array<{
    profile: CrewMemberProfile;
    match_score: number;
    strengths: string[];
    concerns?: string[];
    recommendation: 'highly_recommended' | 'recommended' | 'consider' | 'not_suitable';
  }>;
}

export interface SkillAssessment {
  skill: string;
  level: number;
  assessment_type: 'self_reported' | 'peer_reviewed' | 'project_based' | 'verified';
  evidence: string[];
  last_updated: string;
  trend: 'improving' | 'stable' | 'declining';
}

// Talent Agent Components

// Crew Member Profile Card
export const CrewMemberProfileCard: React.FC<{
  profile: CrewMemberProfile;
  compact?: boolean;
  className?: string;
}> = ({ profile, compact = false, className }) => {
  const getAvailabilityColor = (status: string) => {
    switch (status) {
      case 'available': return 'text-green-400 bg-green-500/20 border-green-400/30';
      case 'limited': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'booked': return 'text-red-400 bg-red-500/20 border-red-400/30';
      case 'unavailable': return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  if (compact) {
    return (
      <Card className={cn(
        "p-4 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm hover:scale-105 transition-transform",
        className
      )}>
        <div className="flex items-center gap-3">
          <Avatar className="w-12 h-12">
            <AvatarImage src={profile.avatar} alt={profile.name} />
            <AvatarFallback>{profile.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
          </Avatar>
          
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-white truncate">{profile.name}</h4>
            <p className="text-sm text-gray-400 truncate">{profile.title}</p>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={getAvailabilityColor(profile.availability.status)} size="sm">
                {profile.availability.status}
              </Badge>
              <div className="flex items-center gap-1 text-xs text-purple-400">
                <Star className="w-3 h-3" />
                <span>{profile.performance_score}/100</span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn(
      "p-6 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-start gap-4">
          <Avatar className="w-16 h-16">
            <AvatarImage src={profile.avatar} alt={profile.name} />
            <AvatarFallback className="text-lg">
              {profile.name.split(' ').map(n => n[0]).join('')}
            </AvatarFallback>
          </Avatar>
          
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-white">{profile.name}</h3>
                <p className="text-purple-400 font-medium">{profile.title}</p>
                <div className="flex items-center gap-2 mt-1 text-sm text-gray-400">
                  <MapPin className="w-4 h-4" />
                  <span>{profile.location}</span>
                  <div className="w-1 h-1 bg-gray-400 rounded-full" />
                  <span>{profile.experience_years} years experience</span>
                </div>
              </div>
              
              <Badge className={getAvailabilityColor(profile.availability.status)}>
                {profile.availability.status}
              </Badge>
            </div>
            
            {profile.bio && (
              <p className="text-sm text-gray-300 mt-3 line-clamp-2">
                {profile.bio}
              </p>
            )}
          </div>
        </div>

        <QuickStats
          variant="talent"
          columns={3}
          stats={[
            {
              label: "Performance Score",
              value: `${profile.performance_score}/100`,
              icon: Star,
              trend: profile.performance_score >= 85 ? { direction: 'up', value: 'High' } : undefined
            },
            {
              label: "Projects Completed",
              value: profile.projects_completed,
              icon: Briefcase
            },
            {
              label: "Rate Range",
              value: `$${profile.rate.min}-${profile.rate.max}/${profile.rate.per}`,
              icon: TrendingUp
            }
          ]}
        />

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Top Skills</h4>
          <div className="flex flex-wrap gap-2">
            {profile.skills.slice(0, 6).map((skill, index) => (
              <Badge key={index} variant="outline" className="text-purple-400 border-purple-400/30">
                {skill.name} ({skill.proficiency}/10)
              </Badge>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Specialties</h4>
          <div className="flex flex-wrap gap-2">
            {profile.specialties.map((specialty, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {specialty}
              </Badge>
            ))}
          </div>
        </div>

        {profile.union_status && (
          <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium text-white">Union Status</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {profile.union_status.unions.map((union, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {union}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {profile.contact.email && (
            <Button size="sm" variant="outline" className="flex-1">
              <Mail className="w-4 h-4 mr-2" />
              Email
            </Button>
          )}
          {profile.contact.phone && (
            <Button size="sm" variant="outline" className="flex-1">
              <Phone className="w-4 h-4 mr-2" />
              Call
            </Button>
          )}
          <Button size="sm" variant="outline">
            <ExternalLink className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};

// Skill Assessment Display
export const SkillAssessmentCard: React.FC<{
  assessments: SkillAssessment[];
  className?: string;
}> = ({ assessments, className }) => {
  const getAssessmentIcon = (type: string) => {
    switch (type) {
      case 'self_reported': return User;
      case 'peer_reviewed': return Users;
      case 'project_based': return Briefcase;
      case 'verified': return CheckCircle;
      default: return Activity;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return 'text-green-400';
      case 'stable': return 'text-blue-400';
      case 'declining': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/20 rounded-lg border border-purple-500/30">
            <Award className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Skill Assessment</h3>
            <p className="text-sm text-gray-400">Comprehensive skill evaluation</p>
          </div>
        </div>

        <div className="space-y-4">
          {assessments.map((assessment, index) => {
            const Icon = getAssessmentIcon(assessment.assessment_type);
            return (
              <div key={index} className="p-4 bg-gray-800/50 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-purple-400" />
                    <div>
                      <h4 className="font-medium text-white">{assessment.skill}</h4>
                      <p className="text-xs text-gray-400 capitalize">
                        {assessment.assessment_type.replace('_', ' ')} assessment
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <div className={cn("text-lg font-bold", getTrendColor(assessment.trend))}>
                      {assessment.level}/10
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {assessment.trend}
                    </Badge>
                  </div>
                </div>

                <ProgressBar
                  value={assessment.level * 10}
                  variant="talent"
                  size="sm"
                />

                <div className="space-y-2">
                  <h5 className="text-xs font-medium text-gray-300">Evidence</h5>
                  <div className="space-y-1">
                    {assessment.evidence.slice(0, 3).map((evidence, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-400">{evidence}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="text-xs text-gray-500">
                  Last updated: {new Date(assessment.last_updated).toLocaleDateString()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};

// Availability Calendar Display
export const AvailabilityCalendarCard: React.FC<{
  availability: AvailabilityStatus;
  schedule?: Array<{
    date: string;
    status: 'available' | 'booked' | 'tentative';
    project?: string;
  }>;
  className?: string;
}> = ({ availability, schedule = [], className }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-500 text-white';
      case 'booked': return 'bg-red-500 text-white';
      case 'tentative': return 'bg-yellow-500 text-black';
      default: return 'bg-gray-500 text-white';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/20 rounded-lg border border-purple-500/30">
            <Calendar className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Availability</h3>
            <p className="text-sm text-gray-400">Current schedule and booking status</p>
          </div>
        </div>

        <StatusIndicator
          status={availability.status === 'available' ? 'success' : 
                 availability.status === 'limited' ? 'warning' : 
                 availability.status === 'booked' ? 'error' : 'info'}
          label={`Currently ${availability.status}`}
          description={availability.notes}
        />

        {availability.next_available && (
          <div className="p-3 bg-purple-500/10 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium text-white">Next Available</span>
            </div>
            <p className="text-sm text-gray-300">
              {new Date(availability.next_available).toLocaleDateString()}
            </p>
          </div>
        )}

        {availability.hourly_capacity && (
          <MetricCard
            title="Weekly Capacity"
            value={`${availability.hourly_capacity}h`}
            variant="talent"
            size="sm"
            icon={Clock}
          />
        )}

        {schedule.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-300">Upcoming Schedule</h4>
            <div className="space-y-2">
              {schedule.slice(0, 5).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-3 h-3 rounded-full",
                      getStatusColor(item.status)
                    )} />
                    <span className="text-sm text-gray-300">
                      {new Date(item.date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    {item.project || item.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {availability.calendar_url && (
          <Button size="sm" className="w-full">
            <Calendar className="w-4 h-4 mr-2" />
            View Full Calendar
          </Button>
        )}
      </div>
    </Card>
  );
};

// Role Matching Indicator
export const RoleMatchingCard: React.FC<{
  data: RoleMatchingData;
  className?: string;
}> = ({ data, className }) => {
  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'highly_recommended': return 'text-green-400 bg-green-500/20 border-green-400/30';
      case 'recommended': return 'text-blue-400 bg-blue-500/20 border-blue-400/30';
      case 'consider': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'not_suitable': return 'text-red-400 bg-red-500/20 border-red-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/20 rounded-lg border border-purple-500/30">
            <Users className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Role Matching</h3>
            <p className="text-sm text-gray-400">{data.role}</p>
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Requirements</h4>
          <div className="space-y-1">
            {data.requirements.map((req, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">{req}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">
            Top Candidates ({data.candidates.length})
          </h4>
          {data.candidates.slice(0, 3).map((candidate, index) => (
            <div key={index} className="p-4 bg-gray-800/50 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar className="w-10 h-10">
                    <AvatarImage src={candidate.profile.avatar} alt={candidate.profile.name} />
                    <AvatarFallback className="text-sm">
                      {candidate.profile.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h5 className="font-medium text-white">{candidate.profile.name}</h5>
                    <p className="text-sm text-gray-400">{candidate.profile.title}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-lg font-bold text-purple-400">
                    {candidate.match_score}%
                  </div>
                  <Badge className={getRecommendationColor(candidate.recommendation)}>
                    {candidate.recommendation.replace('_', ' ')}
                  </Badge>
                </div>
              </div>

              <ProgressBar
                value={candidate.match_score}
                variant="talent"
                label="Match Score"
                size="sm"
              />

              <div className="flex flex-wrap gap-1">
                {candidate.strengths.slice(0, 3).map((strength, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs text-green-400 border-green-400/30">
                    {strength}
                  </Badge>
                ))}
              </div>

              {candidate.concerns && candidate.concerns.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {candidate.concerns.slice(0, 2).map((concern, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs text-yellow-400 border-yellow-400/30">
                      ⚠ {concern}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <Button className="w-full" size="sm">
          <Search className="w-4 h-4 mr-2" />
          View All Candidates
        </Button>
      </div>
    </Card>
  );
};

// Portfolio Showcase
export const PortfolioShowcaseCard: React.FC<{
  portfolio: PortfolioItem[];
  className?: string;
}> = ({ portfolio, className }) => {
  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'video': return Film;
      case 'audio': return Headphones;
      case 'image': return Camera;
      case 'document': return BookOpen;
      default: return ExternalLink;
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/20 rounded-lg border border-purple-500/30">
            <Briefcase className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Portfolio</h3>
            <p className="text-sm text-gray-400">{portfolio.length} items</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {portfolio.slice(0, 4).map((item, index) => {
            const Icon = getMediaIcon(item.type);
            return (
              <div key={index} className="group relative overflow-hidden rounded-lg bg-gray-800/50 hover:bg-gray-800/70 transition-colors cursor-pointer">
                {item.thumbnail ? (
                  <div className="aspect-video relative">
                    <img
                      src={item.thumbnail}
                      alt={item.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                  </div>
                ) : (
                  <div className="aspect-video bg-gray-800/50 flex items-center justify-center">
                    <Icon className="w-8 h-8 text-purple-400" />
                  </div>
                )}
                
                <div className="p-3">
                  <h5 className="font-medium text-white text-sm truncate">{item.title}</h5>
                  <div className="flex items-center gap-2 mt-1">
                    {item.role && (
                      <span className="text-xs text-gray-400">{item.role}</span>
                    )}
                    {item.year && (
                      <>
                        <div className="w-1 h-1 bg-gray-400 rounded-full" />
                        <span className="text-xs text-gray-400">{item.year}</span>
                      </>
                    )}
                  </div>
                  {item.awards && item.awards.length > 0 && (
                    <div className="flex items-center gap-1 mt-1">
                      <Award className="w-3 h-3 text-yellow-400" />
                      <span className="text-xs text-yellow-400">Award Winner</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {portfolio.length > 4 && (
          <Button size="sm" variant="outline" className="w-full">
            View All {portfolio.length} Items
          </Button>
        )}
      </div>
    </Card>
  );
};

// Union Status Display
export const UnionStatusCard: React.FC<{
  unionInfo: UnionInfo;
  className?: string;
}> = ({ unionInfo, className }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20 border-green-400/30';
      case 'pending': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'inactive': return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-purple-500/10 border-purple-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-500/20 rounded-lg border border-purple-500/30">
              <Shield className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Union Status</h3>
              <p className="text-sm text-gray-400">Professional memberships</p>
            </div>
          </div>
          
          <Badge className={getStatusColor(unionInfo.status)}>
            {unionInfo.status}
          </Badge>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Union Memberships</h4>
          <div className="space-y-2">
            {unionInfo.unions.map((union, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                <span className="text-sm text-gray-300">{union}</span>
                <CheckCircle className="w-4 h-4 text-green-400" />
              </div>
            ))}
          </div>
        </div>

        {unionInfo.member_since && (
          <div className="p-3 bg-purple-500/10 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium text-white">Member Since</span>
            </div>
            <p className="text-sm text-gray-300">
              {new Date(unionInfo.member_since).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};