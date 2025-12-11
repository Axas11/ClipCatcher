import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, Play, Heart, Eye, Coins } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { showSuccess, showError } from "@/utils/toast";

const Dashboard = () => {
  const { toast } = useToast();
  const [tokens, setTokens] = useState(100);
  const [clips, setClips] = useState([
    {
      id: 1,
      title: "EPIC 4K Clutch in Valorant",
      thumbnail: "/placeholder.svg",
      views: 12500,
      likes: 890,
      duration: "0:32"
    },
    {
      id: 2,
      title: "First Blood of the Stream!",
      thumbnail: "/placeholder.svg",
      views: 8700,
      likes: 650,
      duration: "0:18"
    },
    {
      id: 3,
      title: "Unbelievable Ace Play",
      thumbnail: "/placeholder.svg",
      views: 15200,
      likes: 1200,
      duration: "0:45"
    }
  ]);
  const [videos, setVideos] = useState([]);

  const handleUpload = () => {
    showSuccess("Video uploaded successfully! Processing will begin shortly.");
  };

  const handleTokenPurchase = () => {
    // In a real app, this would open a payment modal
    toast({
      title: "Token Purchase",
      description: "Redirecting to payment page...",
    });
  };

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-600">Welcome back! Ready to create some amazing clips?</p>
      </div>

      {/* Token Status */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Your Tokens</span>
            <Button onClick={handleTokenPurchase} variant="outline">
              <Coins className="mr-2 h-4 w-4" />
              Buy More Tokens
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center">
            <div className="text-4xl font-bold mr-4">{tokens}</div>
            <div className="text-gray-500">tokens remaining</div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Tokens are used to process your videos. Upload longer videos to earn more!
          </p>
        </CardContent>
      </Card>

      {/* Upload Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Upload New Video</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium">Upload your stream</h3>
            <p className="mt-1 text-sm text-gray-500">
              Drag and drop your video file here, or click to browse
            </p>
            <Button className="mt-4" onClick={handleUpload}>
              Select File
            </Button>
            <p className="mt-2 text-xs text-gray-500">
              Max file size: 5GB. Supported formats: MP4, MOV, AVI
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Recent Clips */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clips.map((clip) => (
          <Card key={clip.id}>
            <img 
              src={clip.thumbnail} 
              alt={clip.title} 
              className="w-full h-48 object-cover rounded-t-lg"
            />
            <CardContent className="p-4">
              <h3 className="font-semibold mb-2">{clip.title}</h3>
              <div className="flex justify-between text-sm text-gray-500">
                <div className="flex items-center">
                  <Eye className="mr-1 h-4 w-4" />
                  {clip.views}
                </div>
                <div className="flex items-center">
                  <Heart className="mr-1 h-4 w-4" />
                  {clip.likes}
                </div>
                <div className="flex items-center">
                  <Play className="mr-1 h-4 w-4" />
                  {clip.duration}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;