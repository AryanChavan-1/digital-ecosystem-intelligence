import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../../components/ui/Card";
import { ApiError } from "../../api/client";

const signupSchema = z.object({
  fullName: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  workspaceName: z.string().min(2, "Workspace name must be at least 2 characters"),
});

type SignupFormValues = z.infer<typeof signupSchema>;

export function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      workspaceName: "",
    },
  });

  const onSubmit = async (values: SignupFormValues) => {
    try {
      setErrorMessage(null);
      await signup(values.email, values.password, values.fullName, values.workspaceName);
      navigate("/onboarding");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message || "Failed to create account");
      } else {
        setErrorMessage("An unexpected error occurred during registration");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50">
      <Card className="w-full max-w-md shadow-md border-slate-200">
        <CardHeader className="text-center space-y-1">
          <div className="inline-flex items-center justify-center h-10 w-10 rounded-xl bg-indigo-600 text-white font-bold text-lg mx-auto mb-2">
            DE
          </div>
          <CardTitle className="text-2xl font-bold">Create Workspace Account</CardTitle>
          <CardDescription>
            Join Indian D2C brand teams uncovering emerging consumer signals
          </CardDescription>
        </CardHeader>
        <CardContent>
          {errorMessage && (
            <div className="mb-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700 border border-rose-200">
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Full Name</label>
              <Input
                type="text"
                placeholder="Aryan Chavan"
                {...register("fullName")}
                className={errors.fullName ? "border-rose-500" : ""}
              />
              {errors.fullName && (
                <p className="text-xs text-rose-600">{errors.fullName.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Work Email</label>
              <Input
                type="email"
                placeholder="aryan@d2cbrand.in"
                {...register("email")}
                className={errors.email ? "border-rose-500" : ""}
              />
              {errors.email && (
                <p className="text-xs text-rose-600">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Workspace / Brand Name</label>
              <Input
                type="text"
                placeholder="Aura Organics D2C"
                {...register("workspaceName")}
                className={errors.workspaceName ? "border-rose-500" : ""}
              />
              {errors.workspaceName && (
                <p className="text-xs text-rose-600">{errors.workspaceName.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Password</label>
              <Input
                type="password"
                placeholder="••••••••"
                {...register("password")}
                className={errors.password ? "border-rose-500" : ""}
              />
              {errors.password && (
                <p className="text-xs text-rose-600">{errors.password.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Start Free Workspace
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2 text-center text-xs text-slate-500">
          <div>
            Already have an account?{" "}
            <Link to="/login" className="text-indigo-600 font-semibold hover:underline">
              Sign in
            </Link>
          </div>
          <div className="text-[11px] text-slate-400">
            By signing up, you agree to DPDP non-PII terms & ASCI disclosure obligations
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
