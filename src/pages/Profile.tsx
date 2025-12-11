import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Play, Heart, Eye, Calendar } from 'lucide-react';

const Profile = () => {
  const [user] = useState({
    id: 1,
    username: "ValorantPro",
    email: "pro@valorant.com",
    avatar: "/placeholder.svg",
    clipsCount: 24,
    followers: 1250,
    following: 89
  });

  const [clips] = useState([
    {
      id: 1,
      title: "EPIC 4K Clutch in Valorant",
      thumbnail: "/placeholder.svg",
      views: 12500,
      likes: 890,
      date: "2023-05-15"
    },
    {
      id: 2,
      title: "First Blood of the Stream!",
      thumbnail: "/placeholder.svg",
      views: 8700,
      likes: 650,
      date: "2023-05-10"
    },
    {
      id: 3,
      title: "Unbelievable Ace Play",
      thumbnail: "/placeholder.svg",
      views: 15200,
      likes: 1200,
      date: "2023-05-05"
    }
  ]);

  return (
    <div className="container mx-auto py-8">
      {/* Profile Header */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row items-center md:items-start">
            <Avatar className="h-24 w-24 mb-4 md:mb-0 md:mr-6">
              <AvatarImage src={user.avatar} alt={user.username} />
              <AvatarFallback>{user.username.charAt(0)}</AvatarFallback>
            </Avatar>
            
            <div className="text-center md:text-left flex-1">
              <h1 className="text-3xl font-bold">{user.username}</h1>
              <p className="text-gray-600 mb-4">{user.email}</p>
              
              <div className="flex justify-center md:justify-start space-x-6 mb-4">
                <div className="text-center">
                  <div className="font-bold text-xl">{user.clipsCount}</div>
                  <div className="text-gray-500">Clips</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-xl">{user.followers.toLocaleString()}</div>
                  <div className="text-gray-500">Followers</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-xl">{user.following}</div>
                  <div className="text-gray-500">Following</div>
                </div>
              </div>
              
              <Button>Follow</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Clips Section */}
      <Tabs defaultValue="top" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="top">Top Clips</TabsTrigger>
          <TabsTrigger value="recent">Recent Clips</TabsTrigger>
        </TabsList>
        
        <TabsContent value="top">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clips.map((clip) => (
              <Card key={clip.id} className="overflow-hidden">
                <div className="relative">
                  <img 
                    src={clip.thumbnail} 
                    alt={clip.title} 
                    className="w-full h-48 object-cover"
                  />
                  <div className="absolute top-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-sm">
                    <Play className="inline h-3 w-3 mr-1" />
                    0:32
                  </div>
                </div>
                
                <CardContent className="p-4">
                  <h3 className="font-semibold mb-2">{clip.title}</h3>
                  
                  <div className="flex justify-between text-sm text-gray-500 mb-2">
                    <div className="flex items-center">
                      <Eye className="mr-1 h-4 w-4" />
                      {clip.views.toLocaleString()}
                    </div>
                    <div className="flex items-center">
                      <Heart className="mr-1 h-4 w-4" />
                      {clip.likes.toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="flex items-center text-xs text-gray-500">
                    <Calendar className="mr-1 h-3 w-3" />
                    {new Date(clip.date).toLocaleDateString()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        
        <TabsContent value="recent">
          <div className="text-center py-12 text-gray-500">
            <p>No recent clips to display.</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Profile;