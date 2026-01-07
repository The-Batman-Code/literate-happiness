"""Adzuna job search tools for Google ADK agents.

These tools wrap the Adzuna API service for use by AI agents.
All tools are async and use dependency injection for the service instance.
"""

from typing import cast

from src.app.containers import AppDependencies
from src.app.core import logger
from src.app.schemas.adzuna import (
    AdzunaCategoriesParams,
    AdzunaGeodataParams,
    AdzunaHistogramParams,
    AdzunaHistoricalParams,
    AdzunaSearchParams,
    AdzunaTopCompaniesParams,
)
from src.app.services.adzuna.service import AdzunaService


async def search_adzuna_jobs(
    query: str,
    location: str | None = None,
    country: str = "us",
    max_results: int = 10,
) -> str:
    """Search for job listings using Adzuna API.

    This tool searches for current job openings based on keywords and location.
    Returns formatted job listings with titles, companies, locations, and salaries.

    Args:
        query: Keywords to search for (e.g., "Python developer", "Data scientist")
        location: Optional location (e.g., "San Francisco", "Remote")
        country: Country code (default: "us")
        max_results: Maximum results to return (1-50, default: 10)

    Returns:
        Formatted string with job listings
    """
    logger.bind(query=query, location=location, country=country).info(
        "Executing Adzuna job search",
    )

    adzuna = cast(AdzunaService, await AppDependencies.adzuna_service.resolve())  # type: ignore

    params = AdzunaSearchParams(
        what=query,
        where=location,
        country=country,
        page=1,
        results_per_page=max_results,
    )

    try:
        response = await adzuna.search_jobs(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception("Adzuna job search failed")
        return f"Error searching for jobs: {e}"

    if not response.results:
        return f"No jobs found for query: {query}"

    # Format results
    output = [f"Found {response.count} jobs for '{query}':"]
    output.append("")

    for idx, job in enumerate(response.results, 1):
        output.append(f"{idx}. {job.title}")
        output.append(f"   Company: {job.company.display_name}")
        output.append(f"   Location: {job.location.display_name}")

        if job.salary_min and job.salary_max:
            output.append(
                f"   Salary: ${job.salary_min:,.0f} - ${job.salary_max:,.0f}",
            )

        if job.description:
            # No truncation as requested
            output.append(f"   Description: {job.description}")

        output.append("")

    return "\n".join(output)


async def analyze_salary_trends(
    job_title: str,
    location: str | None = None,
    country: str = "us",
) -> str:
    """Analyze salary distribution for a specific job title.

    This tool provides salary range analysis including min, max, median,
    and distribution across salary bands for a given job title.

    Args:
        job_title: Job title to analyze (e.g., "Software Engineer")
        location: Optional location filter
        country: Country code (default: "us")

    Returns:
        Formatted salary analysis string
    """
    logger.bind(job_title=job_title, location=location).info(
        "Analyzing Adzuna salary trends",
    )

    adzuna = cast(AdzunaService, await AppDependencies.adzuna_service.resolve())  # type: ignore

    params = AdzunaHistogramParams(
        what=job_title,
        where=location,
        country=country,
    )

    try:
        response = await adzuna.get_salary_histogram(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna salary analysis failed",
        )
        return f"Error analyzing salary trends: {e}"

    if not response.histogram:
        return f"No salary data available for: {job_title}"

    # Format results
    output = [f"Salary Analysis for '{job_title}':"]
    output.append("")
    output.append("Salary Distribution (Annual):")

    # Sort histogram by salary bucket (the key)
    sorted_histogram = sorted(response.histogram.items(), key=lambda x: int(x[0]))
    total_jobs = sum(response.histogram.values())

    for salary_min, count in sorted_histogram:
        count_percent = (count / total_jobs) * 100
        output.append(
            f"  ${int(salary_min):,.0f}+: {count} jobs ({count_percent:.1f}%)",
        )

    return "\n".join(output)


async def get_top_hiring_companies(
    job_category: str | None = None,
    location: str | None = None,
    country: str = "us",
) -> str:
    """Get the top companies currently hiring.

    This tool returns the top 5 companies with the most job openings,
    optionally filtered by category and location.

    Args:
        job_category: Optional job category filter (e.g., "IT Jobs")
        location: Optional location filter
        country: Country code (default: "us")

    Returns:
        Formatted list of top hiring companies
    """
    logger.bind(category=job_category, location=location).info(
        "Fetching top hiring companies from Adzuna",
    )

    adzuna = cast(AdzunaService, await AppDependencies.adzuna_service.resolve())  # type: ignore

    params = AdzunaTopCompaniesParams(
        what=job_category,
        where=location,
        country=country,
    )

    try:
        response = await adzuna.get_top_companies(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna top companies fetch failed",
        )
        return f"Error fetching top companies: {e}"

    if not response.leaderboard:
        return "No company data available"

    # Format results
    output = ["Top Hiring Companies:"]
    output.append("")

    for idx, company in enumerate(response.leaderboard, 1):
        output.append(
            f"{idx}. {company.name} - {company.count} open positions",
        )

    return "\n".join(output)


async def list_job_categories(country: str = "us") -> str:
    """List all available job categories for a country.

    This tool returns a list of job categories that can be used to filter
    other job search tools.

    Args:
        country: Country code (default: "us")

    Returns:
        Formatted list of job categories and their search tags
    """
    logger.bind(country=country).info("Listing Adzuna job categories")

    adzuna = cast(AdzunaService, await AppDependencies.adzuna_service.resolve())  # type: ignore

    params = AdzunaCategoriesParams(country=country)

    try:
        response = await adzuna.get_categories(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna categories fetch failed",
        )
        return f"Error listing categories: {e}"

    if not response.results:
        return "No categories available"

    output = [f"Available Job Categories for {country.upper()}:"]
    output.append("")
    for cat in response.results:
        output.append(f"- {cat.label} (Tag: {cat.tag})")

    return "\n".join(output)


async def get_regional_job_stats(
    location: str | None = None,
    country: str = "us",
) -> str:
    """Get job counts and statistics by sub-region.

    This tool provides a breakdown of how many jobs are available in
    different cities or areas within a larger region.

    Args:
        location: Parent location (e.g., "California", "Texas")
        country: Country code (default: "us")

    Returns:
        Formatted string with regional job counts
    """
    logger.bind(location=location, country=country).info("Fetching Adzuna regional stats")

    adzuna = cast(AdzunaService, await AppDependencies.adzuna_service.resolve())  # type: ignore

    params = AdzunaGeodataParams(where=location, country=country)

    try:
        response = await adzuna.get_geodata(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna geodata fetch failed",
        )
        return f"Error fetching regional stats: {e}"

    if not response.locations:
        return "No regional data available"

    output = [f"Regional Job Stats for '{location or country}':"]
    output.append("")
    for loc in response.locations:
        output.append(f"- {loc.location.display_name}: {loc.count} jobs")

    return "\n".join(output)


async def get_historical_salary_trends(
    job_title: str,
    location: str | None = None,
    country: str = "us",
    months: int = 12,
) -> str:
    """Get historical average salary trends for a job title.

    This tool returns average salary data month-by-month for the past 12-24 months.

    Args:
        job_title: Job title to research
        location: Optional location filter
        country: Country code (default: "us")
        months: Number of months of history (1-24, default: 12)

    Returns:
        Formatted historical salary trend string
    """
    logger.bind(job_title=job_title, location=location, months=months).info(
        "Fetching Adzuna historical trends",
    )

    adzuna = cast(AdzunaService, await AppDependencies.adzuna_service.resolve())  # type: ignore

    params = AdzunaHistoricalParams(
        what=job_title,
        where=location,
        country=country,
        months=months,
    )

    try:
        response = await adzuna.get_historical_data(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna historical data fetch failed",
        )
        return f"Error fetching historical trends: {e}"

    if not response.month:
        return f"No historical data available for: {job_title}"

    output = [f"Historical Salary Trends for '{job_title}':"]
    output.append("")

    # Sort by month (key is YYYY-MM)
    sorted_history = sorted(response.month.items())

    for month_str, salary in sorted_history:
        output.append(f"- {month_str}: ${salary:,.0f}")

    return "\n".join(output)


__all__ = [
    "search_adzuna_jobs",
    "analyze_salary_trends",
    "get_top_hiring_companies",
    "list_job_categories",
    "get_regional_job_stats",
    "get_historical_salary_trends",
]
