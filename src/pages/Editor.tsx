import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Play, Pause, Volume2, VolumeX, Download, Share } from 'lucide-react';

const Editor = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [volume, setVolume] = useState(80);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(32); // 32 seconds

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const toggleSubtitles = () => {
    setShowSubtitles(!showSubtitles);
  };

  const handleVolumeChange = (value) => {
    setVolume(value[0]);
  };

  const handleTimeChange = (value) => {
    setCurrentTime(value[0]);
  };

  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Clip Editor</h1>
        <p className="text-gray-600">Edit your clip before sharing</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Preview Section */}
        <div className="lg:col-span-2">
          <Card>
            <CardContent className="p-0">
              <div className="relative bg-black aspect-[9/16] rounded-lg overflow-hidden">
                {/* Facecam layer */}
                <div className="absolute top-0 left-0 right-0 h-1/3 bg-gray-800">
                  <div className="bg-gray-700 w-full h-full flex items-center justify-center">
                    <span className="text-white">Facecam</span>
                  </div>
                </div>
                
                {/* Gameplay layer */}
                <div className="absolute bottom-0 left-0 right-0 h-2/3 bg-gray-900">
                  <div className="bg-gray-800 w-full h-full flex items-center justify-center">
                    <span className="text-white">Gameplay</span>
                  </div>
                  
                  {/* Subtitles */}
                  {showSubtitles && (
                    <div className="absolute bottom-4 left-0 right-0 text-center">
                      <div className="inline-block bg-black bg-opacity-70 text-white px-4 py-2 rounded-lg">
                        "That was an incredible play!"
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Play/Pause overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  {!isPlaying && (
                    <Button 
                      size="icon" 
                      className="h-16 w-16 rounded-full bg-white bg-opacity-80 hover:bg-opacity-100"
                      onClick={togglePlay}
                    >
                      <Play className="h-8 w-8 text-black" />
                    </Button>
                  )}
                </div>
              </div>
              
              {/* Controls */}
              <div className="p-4">
                <div className="mb-4">
                  <Slider 
                    value={[currentTime]} 
                    max={duration} 
                    step={1}
                    onValueChange={handleTimeChange}
                  />
                  <div className="flex justify-between text-sm text-gray-500 mt-1">
                    <span>{Math.floor(currentTime / 60)}:{String(currentTime % 60).padStart(2, '0')}</span>
                    <span>{Math.floor(duration / 60)}:{String(duration % 60).padStart(2, '0')}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <Button 
                      size="icon" 
                      variant="ghost"
                      onClick={togglePlay}
                    >
                      {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                    </Button>
                    
                    <div className="flex items-center space-x-2">
                      {volume > 0 ? 
                        <Volume2 className="h-5 w-5" /> : 
                        <VolumeX className="h-5 w-5" />
                      }
                      <Slider 
                        className="w-24" 
                        value={[volume]} 
                        max={100} 
                        step={1}
                        onValueChange={handleVolumeChange}
                      />
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Label htmlFor="subtitles" className="flex items-center space-x-2">
                      <span>Subtitles</span>
                      <Switch 
                        id="subtitles" 
                        checked={showSubtitles} 
                        onCheckedChange={toggleSubtitles}
                      />
                    </Label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Settings Panel */}
        <div>
          <Card>
            <CardContent className="p-6">
              <h2 className="text-xl font-bold mb-4">Clip Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium mb-2">Clip Title</h3>
                  <input 
                    type="text" 
                    defaultValue="EPIC 4K Clutch in Valorant" 
                    className="w-full p-2 border rounded"
                  />
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">#valorant</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">#clutch</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">#4k</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">#pro</span>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">Privacy</h3>
                  <select className="w-full p-2 border rounded">
                    <option>Public</option>
                    <option>Unlisted</option>
                    <option>Private</option>
                  </select>
                </div>
                
                <div className="pt-4">
                  <Button className="w-full mb-2">
                    <Download className="mr-2 h-4 w-4" />
                    Save Clip
                  </Button>
                  <Button variant="outline" className="w-full">
                    <Share className="mr-2 h-4 w-4" />
                    Share to Feed
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Editor;