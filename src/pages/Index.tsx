import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Play, Users, TrendingUp, Coins } from 'lucide-react';
import { MadeWithDyad } from '@/components/made-with-dyad';

const Index = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 py-20">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Turn Your Streams Into <span className="text-yellow-300">Viral Clips</span>
            </h1>
            <p className="text-xl mb-8 text-blue-100">
              ClipCatcher automatically detects the best moments in your Valorant streams and turns them into TikTok-ready highlights.
            </p>
            <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              <Button size="lg" className="text-lg py-6 px-8 bg-white text-blue-600 hover:bg-gray-100">
                Get Started Free
              </Button>
              <Button size="lg" variant="outline" className="text-lg py-6 px-8 border-white text-white hover:bg-white hover:text-blue-600">
                <Play className="mr-2 h-6 w-6" />
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Transform your long streams into engaging content with our AI-powered platform
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">Upload</h3>
              <p className="text-gray-600">
                Simply upload your Valorant stream VOD. Our system handles videos up to 5 hours long.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">AI Processing</h3>
              <p className="text-gray-600">
                Our AI detects the most exciting moments - kills, clutches, and hype plays.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Play className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">Share</h3>
              <p className="text-gray-600">
                Edit your clips with our TikTok-style editor and share them with the world.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Token System */}
      <div className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full mb-6">
              <Coins className="mr-2 h-5 w-5" />
              <span className="font-medium">Token-Based System</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Fair Pricing for Streamers</h2>
            <p className="text-xl text-gray-600 mb-12">
              Get 100 free tokens to start. Longer videos use more tokens, but you can earn more through subscriptions.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="text-4xl font-bold text-blue-600 mb-2">100</div>
                  <h3 className="text-xl font-bold mb-2">Free Tokens</h3>
                  <p className="text-gray-600 mb-4">To get you started</p>
                  <Button variant="outline">Sign Up Now</Button>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="text-4xl font-bold text-green-600 mb-2">500</div>
                  <h3 className="text-xl font-bold mb-2">Monthly Plan</h3>
                  <p className="text-gray-600 mb-4">Best value option</p>
                  <Button>Subscribe</Button>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="text-4xl font-bold text-purple-600 mb-2">1000+</div>
                  <h3 className="text-xl font-bold mb-2">Pro Plan</h3>
                  <p className="text-gray-600 mb-4">For heavy streamers</p>
                  <Button variant="secondary">Learn More</Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Go Viral?</h2>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          Join thousands of Valorant streamers who are already using ClipCatcher to grow their audience.
        </p>
        <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
          <Button size="lg" className="text-lg py-6 px-8">
            Start Free Trial
          </Button>
          <Button size="lg" variant="outline" className="text-lg py-6 px-8">
            <Users className="mr-2 h-6 w-6" />
            View Community
          </Button>
        </div>
      </div>

      <MadeWithDyad />
    </div>
  );
};

export default Index;