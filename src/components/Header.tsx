import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Coins, User, Home, TrendingUp, Brain } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const Header = () => {
  const user = {
    username: "ValorantPro",
    tokens: 100,
    avatar: "/placeholder.svg"
  };

  return (
    <header className="border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-bold text-blue-600">
              ClipCatcher
            </Link>
          </div>
          
          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link to="/" className="flex items-center text-gray-600 hover:text-gray-900">
              <Home className="mr-2 h-4 w-4" />
              Home
            </Link>
            <Link to="/feed" className="flex items-center text-gray-600 hover:text-gray-900">
              <TrendingUp className="mr-2 h-4 w-4" />
              Feed
            </Link>
            <Link to="/dashboard" className="flex items-center text-gray-600 hover:text-gray-900">
              <User className="mr-2 h-4 w-4" />
              Dashboard
            </Link>
            <Link to="/ai-algorithm" className="flex items-center text-gray-600 hover:text-gray-900">
              <Brain className="mr-2 h-4 w-4" />
              AI Algorithm
            </Link>
          </nav>
          
          {/* User Section */}
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center bg-gray-100 rounded-full px-3 py-1">
              <Coins className="h-4 w-4 text-yellow-500 mr-1" />
              <span className="font-medium">{user.tokens}</span>
            </div>
            
            <Link to="/profile">
              <Avatar className="h-8 w-8">
                <AvatarImage src={user.avatar} alt={user.username} />
                <AvatarFallback>{user.username.charAt(0)}</AvatarFallback>
              </Avatar>
            </Link>
            
            <Button variant="outline" size="sm" className="hidden md:inline">
              Upload
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;