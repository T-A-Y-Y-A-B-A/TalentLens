"use client";

import { useState, useMemo } from "react";
import { Country, City } from "country-state-city";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandInput,
  CommandItem,
  CommandList,
  CommandEmpty,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function LocationSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (location: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  // Build a flat "City, Country" list once
  const locations = useMemo(() => {
    const countries = Country.getAllCountries();
    const uniqueSet = new Set<string>();
    countries.forEach((country) => {
      const cities = City.getCitiesOfCountry(country.isoCode) || [];
      cities.forEach((city) => {
        uniqueSet.add(`${city.name}, ${country.name}`);
      });
    });
    return Array.from(uniqueSet);
  }, []);

  const filteredLocations = useMemo(() => {
    if (search.length < 2) return [];
    const lowerSearch = search.toLowerCase();
    return locations
      .filter((loc) => loc.toLowerCase().includes(lowerSearch))
      .slice(0, 100);
  }, [search, locations]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger 
        render={<Button variant="outline" role="combobox" className="w-full justify-between" />}
      >
        <span className="truncate">{value || "Search city..."}</span>
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput 
            placeholder="Type at least 2 characters..." 
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>
              {search.length < 2 
                ? "Type at least 2 characters to search" 
                : "No location found."}
            </CommandEmpty>
            {filteredLocations.map((loc) => (
              <CommandItem
                key={loc}
                value={loc}
                onSelect={() => {
                  onChange(loc);
                  setOpen(false);
                  setSearch(""); // clear search on select
                }}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4 shrink-0",
                    value === loc ? "opacity-100" : "opacity-0"
                  )}
                />
                <span className="truncate">{loc}</span>
              </CommandItem>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
