import React from "react";
import { useAuth } from "@/context/AuthContext";

export default function Profile() {
  const { profile, user } = useAuth();
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">My Profile</h1>
      <pre>{JSON.stringify(profile || user, null, 2)}</pre>
    </div>
  );
}