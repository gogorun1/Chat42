/*DEV*/
/* for someone who want to see the website before the realization of f10 */
/* you can use this dev mode */
/* you need also put "VITE_DEV_MODE=true" in .env in fronted */

/*import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode
} from "react";

import { api } from "../lib/api";


export interface User {

  id: number;

  email: string;

  ft_login: string | null;

}



interface AuthContextValue {

  user: User | null;

  loading: boolean;

  login: (
    email:string,
    password:string
  ) => Promise<void>;

  signup: (
    email:string,
    password:string
  ) => Promise<void>;

  logout: () => Promise<void>;

}



const AuthContext =
createContext<AuthContextValue | undefined>(undefined);



const DEV_MODE =
import.meta.env.VITE_DEV_MODE === "true";



const DEV_USER: User = {

  id: 1,

  email: "cat42-dev@42.fr",

  ft_login: "dev-cat"

};



export function AuthProvider(
{
children
}:{
children:ReactNode
}) {


  const [user,setUser] =
  useState<User|null>(null);


  const [loading,setLoading] =
  useState(true);



  useEffect(()=>{


    async function loadUser(){


      // DEV MODE

      if(DEV_MODE){

        setUser(DEV_USER);

        setLoading(false);

        return;

      }



      // REAL BACKEND

      try{

        const currentUser =
        await api.get<User>("/auth/me");


        setUser(currentUser);


      }
      catch{

        setUser(null);

      }
      finally{

        setLoading(false);

      }


    }


    loadUser();


  },[]);




  async function login(
    email:string,
    password:string
  ){


    if(DEV_MODE){

      setUser({
        ...DEV_USER,
        email
      });

      return;

    }



    setUser(
      await api.post<User>(
        "/auth/login",
        {
          email,
          password
        }
      )
    );

  }





  async function signup(
    email:string,
    password:string
  ){


    if(DEV_MODE){

      setUser({
        ...DEV_USER,
        email
      });

      return;

    }



    setUser(
      await api.post<User>(
        "/auth/signup",
        {
          email,
          password
        }
      )
    );

  }





  async function logout(){


    if(DEV_MODE){

      setUser(null);

      return;

    }



    await api.post("/auth/logout");

    setUser(null);


  }




  return (

    <AuthContext.Provider

      value={{
        user,
        loading,
        login,
        signup,
        logout
      }}

    >

      {children}

    </AuthContext.Provider>

  );

}





export function useAuth(){

  const ctx =
  useContext(AuthContext);


  if(!ctx)

    throw new Error(
      "useAuth must be used within AuthProvider"
    );


  return ctx;

}*/


/*the real version with auth 42*/

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../lib/api'

export type UserRole = 'user' | 'moderator' | 'admin'

export interface User {
  id: number
  email: string
  ft_login: string | null
  role: UserRole
  display_name: string | null
  avatar_url: string | null
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<User>('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    setUser(await api.post<User>('/auth/login', { email, password }))
  }

  async function signup(email: string, password: string) {
    setUser(await api.post<User>('/auth/signup', { email, password }))
  }

  async function logout() {
    await api.post('/auth/logout')
    setUser(null)
  }

  async function refreshUser() {
    setUser(await api.get<User>('/auth/me'))
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}