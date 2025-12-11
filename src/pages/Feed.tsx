import React, { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Heart, MessageCircle, Share, Play, Eye } from 'lucide-react';

const Feed = () => {
  const [clips, setClips] = useState([
    {
      id: 1,
      title: "EPIC 4K Clutch in Valorant",
      username: "ProPlayer123",
      views: 12500,
      likes: 890,
      comments: 42,
      thumbnail: "/placeholder.svg",
      duration: "0:32"
    },
    {
      id: 2,
      title: "First Blood of the Stream!",
      username: "ValorantMaster",
      views: 8700,
      likes: 650,
      comments: 28,
      thumbnail: "/placeholder.svg",
      duration: "0:18"
    },
    {
      id: 3,
      title: "Unbelievable Ace Play",
      username: "ClutchKing",
      views: 15200,
      likes: 1200,
      comments: 67,
      thumbnail: "/placeholder.svg",
      duration: "0:45"
    }
  ]);

  const handleLike = (id) => {
    setClips(clips.map(clip => 
      clip.id === id ? { ...clip, likes: clip.likes + 1 } : clip
    ));
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Trending Clips</h1>
      <div className="space-y-6">
        {clips.map((clip) => (
          <Card key={clip.id} className="overflow-hidden">
            <div className="md:flex">
              <div className="md:w-1/2 relative">
                <img 
                  src={clip.thumbnail} 
                  alt={clip.title} 
                  className="w-full h-64 md:h-full object-cover" 
                />
                <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-sm">
                  {clip.duration}
                </div>
                <Button 
                  size="icon" 
                  className="absolute top-2 right-2 bg-black bg-opacity-50 hover:bg-opacity-75"
                >
                  <Play className="h-4 w-4 text-white" />
                </Button>
              </div>
              <div className="md:w-1/2 p-6">
                <h2 className="text-xl font-bold mb-2">{clip.title}</h2>
                <p className="text-gray-600 mb-4">by {clip.username}</p>
                <div className="flex space-x-4 mb-6">
                  <div className="flex items-center text-gray-500">
                    <Eye className="mr-1 h-4 w-4" />
                    {clip.views.toLocaleString()}
                  </div>
                  <div className="flex items-center text-gray-500">
                    <Heart className="mr-1 h-4 w-4" />
                    {clip.likes.toLocaleString()}
                  </div>
                  <div className="flex items-center text-gray-500">
                    <MessageCircle className="mr-1 h-4 w-4" />
                    {clip.comments}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    onClick={() => handleLike(clip.id)}
                    className="flex items-center"
                  >
                    <Heart className="mr-2 h-4 w-4" />
                    Like
                  </Button>
                  <Button variant="outline" className="flex items-center">
                    <MessageCircle className="mr-2 h-4 w-4" />
                    Comment
                  </Button>
                  <Button variant="outline" className="flex items-center">
                    <Share className="mr-2 h-4 w-4" />
                    Share
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Feed;