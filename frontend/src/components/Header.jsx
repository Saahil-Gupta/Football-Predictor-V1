import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Header() {
    const { pathname } = useLocation();

    const navItems = [
        { name: "Home", path: "/" },
        { name: "EPL", path: "/epl" },
        { name: "LaLiga", path: "/laliga" },
    ];

    return (
        <header className="bg-white shadow-md sticky top-0 z-50">
        <nav className="max-w-5xl mx-auto px-2 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-extrabold text-red-600 tracking-tight">
            ⚽ Predictor
            </h1>

            <div className="flex gap-6">
            {navItems.map((item) => (
                <Link
                key={item.path}
                to={item.path}
                className={`text-md font-medium transition-colors ${
                    pathname === item.path
                    ? "text-red-600"
                    : "text-gray-700 hover:text-red-500"
                }`}
                >
                {item.name}
                </Link>
            ))}
            </div>
        </nav>
        </header>
    );
}
