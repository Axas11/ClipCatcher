import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { 
  Play, 
  Pause, 
  Upload, 
  Download, 
  Settings,
  Brain,
  Zap,
  FileText,
  BarChart3,
  Cpu,
  Database
} from 'lucide-react';
import { showSuccess, showError } from "@/utils/toast";

const AIAlgorithm = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [algorithmParams, setAlgorithmParams] = useState({
    sensitivity: 75,
    minLength: 10,
    maxLength: 60,
    detectionType: 'clutch'
  });
  const [results, setResults] = useState<any[]>([]);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadedFile(file);
      showSuccess(`File ${file.name} selected for processing`);
    }
  };

  const handleStartProcessing = () => {
    if (!uploadedFile) {
      showError("Please upload a file first");
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setResults([]);

    // Simulate processing progress
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 5;
        if (newProgress >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          
          // Simulate results
          setResults([
            {
              id: 1,
              title: "EPIC 4K Clutch Play",
              timestamp: "12:34:56",
              duration: "0:32",
              confidence: 98,
              highlights: ["4K Kill", "Clutch", "Headshot"]
            },
            {
              id: 2,
              title: "First Blood of the Match",
              timestamp: "05:22:18",
              duration: "0:18",
              confidence: 92,
              highlights: ["First Blood", "Ace", "Flawless"]
            },
            {
              id: 3,
              title: "Unbelievable Ace Play",
              timestamp: "28:45:33",
              duration: "0:45",
              confidence: 87,
              highlights: ["Ace", "Multi-Kill", "Team Play"]
            }
          ]);
          
          showSuccess("Processing completed successfully!");
          return 100;
        }
        return newProgress;
      });
    }, 200);
  };

  const handleParamChange = (param: string, value: number | string) => {
    setAlgorithmParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 flex items-center">
          <Brain className="mr-3 h-8 w-8 text-blue-600" />
          AI Clip Detection Algorithm
        </h1>
        <p className="text-gray-600">
          Advanced machine learning algorithm for detecting highlight moments in Valorant streams
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="mr-2 h-5 w-5" />
                Algorithm Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="flex items-center">
                  <Zap className="mr-2 h-4 w-4" />
                  Detection Sensitivity: {algorithmParams.sensitivity}%
                </Label>
                <Slider
                  value={[algorithmParams.sensitivity]}
                  onValueChange={(value) => handleParamChange('sensitivity', value[0])}
                  max={100}
                  step={1}
                  className="mt-2"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Higher sensitivity detects more moments but may include false positives
                </p>
              </div>

              <div>
                <Label>Minimum Clip Length: {algorithmParams.minLength}s</Label>
                <Slider
                  value={[algorithmParams.minLength]}
                  onValueChange={(value) => handleParamChange('minLength', value[0])}
                  max={30}
                  min={5}
                  step={1}
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Maximum Clip Length: {algorithmParams.maxLength}s</Label>
                <Slider
                  value={[algorithmParams.maxLength]}
                  onValueChange={(value) => handleParamChange('maxLength', value[0])}
                  max={120}
                  min={30}
                  step={5}
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Detection Type</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {['clutch', 'ace', 'multi-kill', 'first-blood'].map((type) => (
                    <Button
                      key={type}
                      variant={algorithmParams.detectionType === type ? "default" : "outline"}
                      onClick={() => handleParamChange('detectionType', type)}
                      className="text-xs"
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>

              <div>
                <Label className="flex items-center">
                  <FileText className="mr-2 h-4 w-4" />
                  Upload Stream File
                </Label>
                <div className="mt-2">
                  <Input
                    type="file"
                    accept="video/*"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <Label
                    htmlFor="file-upload"
                    className="flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-6 cursor-pointer hover:bg-gray-50"
                  >
                    <Upload className="h-8 w-8 text-gray-400 mb-2" />
                    <span className="text-sm font-medium">
                      {uploadedFile ? uploadedFile.name : "Click to upload video"}
                    </span>
                    <span className="text-xs text-gray-500 mt-1">
                      MP4, MOV, AVI up to 5GB
                    </span>
                  </Label>
                </div>
              </div>

              <Button
                onClick={handleStartProcessing}
                disabled={isProcessing}
                className="w-full"
              >
                {isProcessing ? (
                  <>
                    <Cpu className="mr-2 h-4 w-4 animate-spin" />
                    Processing... {progress}%
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Start Detection
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* System Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="mr-2 h-5 w-5" />
                System Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">CPU Usage</span>
                    <span className="text-sm text-gray-500">65%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '65%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">Memory</span>
                    <span className="text-sm text-gray-500">4.2/8 GB</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '52%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">GPU</span>
                    <span className="text-sm text-gray-500">38%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-600 h-2 rounded-full" style={{ width: '38%' }}></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="mr-2 h-5 w-5" />
                Detection Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isProcessing ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Cpu className="h-12 w-12 text-blue-600 animate-spin mb-4" />
                  <h3 className="text-lg font-medium mb-2">Processing Video</h3>
                  <p className="text-gray-500 mb-4">
                    Analyzing gameplay for highlight moments...
                  </p>
                  <div className="w-full max-w-md">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium">Progress</span>
                      <span className="text-sm text-gray-500">{progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full" 
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ) : results.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="font-medium">Detected Highlights ({results.length})</h3>
                    <Button variant="outline" size="sm">
                      <Download className="mr-2 h-4 w-4" />
                      Export All
                    </Button>
                  </div>
                  
                  <div className="space-y-4">
                    {results.map((result) => (
                      <Card key={result.id}>
                        <CardContent className="p-4">
                          <div className="flex justify-between">
                            <div>
                              <h4 className="font-medium">{result.title}</h4>
                              <div className="flex items-center text-sm text-gray-500 mt-1">
                                <span className="mr-4">⏱️ {result.duration}</span>
                                <span>🕒 {result.timestamp}</span>
                              </div>
                              <div className="flex flex-wrap gap-2 mt-2">
                                {result.highlights.map((highlight: string, idx: number) => (
                                  <Badge key={idx} variant="secondary">
                                    {highlight}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <div className="flex flex-col items-end">
                              <div className="flex items-center">
                                <span className="text-sm font-medium mr-2">Confidence:</span>
                                <Badge 
                                  variant={result.confidence > 90 ? "default" : result.confidence > 75 ? "secondary" : "outline"}
                                >
                                  {result.confidence}%
                                </Badge>
                              </div>
                              <div className="flex space-x-2 mt-4">
                                <Button size="sm">
                                  <Play className="mr-1 h-4 w-4" />
                                  Preview
                                </Button>
                                <Button size="sm" variant="outline">
                                  <Download className="mr-1 h-4 w-4" />
                                  Export
                                </Button>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Brain className="h-16 w-16 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Results Yet</h3>
                  <p className="text-gray-500 max-w-md">
                    Upload a video and run the AI detection algorithm to find highlight moments in your stream.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AIAlgorithm;