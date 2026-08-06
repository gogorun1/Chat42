/*DEV*/
import {
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

}

/* True one
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../lib/api'

export interface User {
  id: number
  email: string
  ft_login: string | null
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
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

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>{children}</AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
 */