import React from "react";
import { AuthPage } from "@/pages/AuthPage";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

function App() {
  const { user, profile, logout, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-muted-foreground">
        Loading...
      </div>
    );
  }

  return (
    <>
      <AuthPage />
      {user && (
        <div className="fixed bottom-4 right-4 flex items-center gap-3 bg-background/80 border rounded-full px-4 py-2 shadow">
          <span className="text-xs text-muted-foreground">
            {profile?.full_name || user.email}
          </span>
          <Button size="sm" variant="outline" onClick={logout}>
            Logout
          </Button>
        </div>
      )}
    </>
  );
}

export default App;
