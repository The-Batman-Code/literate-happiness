"""Adzuna job search tools for Google ADK agents.

These tools wrap the Adzuna API service for use by AI agents.
All tools are async and use dependency injection for the service instance.
"""

from src.app.agents.linkedin_search_agent.schemas import (
    HistoricalTrendsInput,
    JobCategoriesInput,
    JobSearchInput,
    RegionalStatsInput,
    SalaryAnalysisInput,
    TopCompaniesInput,
)
from src.app.containers.app_container import AppDependencies, get_container
from src.app.core import logger
from src.app.schemas.adzuna import (
    AdzunaCategoriesParams,
    AdzunaGeodataParams,
    AdzunaHistogramParams,
    AdzunaHistoricalParams,
    AdzunaSearchParams,
    AdzunaTopCompaniesParams,
)


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
    # Validate with Agent Schema
    agent_input = JobSearchInput(
        query=query,
        location=location,
        country=country,
        max_results=max_results,
    )

    logger.bind(
        query=agent_input.query,
        location=agent_input.location,
        country=agent_input.country,
    ).info(
        "Executing Adzuna job search for '{}' in {}",
        agent_input.query,
        agent_input.location,
    )

    container = get_container()
    adzuna = await container.resolve_provider(AppDependencies.adzuna_service)

    # Map to Service Schema
    params = AdzunaSearchParams(
        what=agent_input.query,
        where=agent_input.location,
        country=agent_input.country,
        page=1,
        results_per_page=agent_input.max_results,
    )

    try:
        response = await adzuna.search_jobs(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception("Adzuna job search failed")
        return f"Error searching for jobs: {e}"

    if not response.results:
        return f"No jobs found for query: {agent_input.query}"

    # Format results
    output = [f"Found {response.count} jobs for '{agent_input.query}':"]
    output.append("")

    for idx, job in enumerate(response.results, 1):
        output.append(f"{idx}. {job.title}")

        company_name = job.company.display_name or "Not Specified"
        output.append(f"   Company: {company_name}")

        location_name = job.location.display_name or "Not Specified"
        output.append(f"   Location: {location_name}")

        output.append(f"   Apply Here: {job.redirect_url}")

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
    # Validate with Agent Schema
    agent_input = SalaryAnalysisInput(
        job_title=job_title,
        location=location,
        country=country,
    )

    logger.bind(
        job_title=agent_input.job_title,
        location=agent_input.location,
    ).info(
        "Analyzing Adzuna salary trends for '{}' in {}",
        agent_input.job_title,
        agent_input.location,
    )

    container = get_container()
    adzuna = await container.resolve_provider(AppDependencies.adzuna_service)

    # Map to Service Schema
    params = AdzunaHistogramParams(
        what=agent_input.job_title,
        where=agent_input.location,
        country=agent_input.country,
    )

    try:
        response = await adzuna.get_salary_histogram(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna salary analysis failed",
        )
        return f"Error analyzing salary trends: {e}"

    if not response.histogram:
        return f"No salary data available for: {agent_input.job_title}"

    # Format results
    output = [f"Salary Analysis for '{agent_input.job_title}':"]
    output.append("")
    output.append("Salary Distribution (Annual):")

    # Sort histogram by salary bucket (the key)
    sorted_histogram = sorted(response.histogram.items(), key=lambda x: int(x[0]))
    total_jobs = sum(response.histogram.values())

    if total_jobs == 0:
        return f"No salary data available for: {agent_input.job_title}"

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
    # Validate with Agent Schema
    agent_input = TopCompaniesInput(
        job_category=job_category,
        location=location,
        country=country,
    )

    logger.bind(
        category=agent_input.job_category,
        location=agent_input.location,
    ).info(
        "Fetching top hiring companies for '{}' in {}",
        agent_input.job_category or "all categories",
        agent_input.location or "all locations",
    )

    container = get_container()
    adzuna = await container.resolve_provider(AppDependencies.adzuna_service)

    # Map to Service Schema
    params = AdzunaTopCompaniesParams(
        what=agent_input.job_category,
        where=agent_input.location,
        country=agent_input.country,
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
    # Validate with Agent Schema
    agent_input = JobCategoriesInput(country=country)

    logger.bind(country=agent_input.country).info(
        "Listing Adzuna job categories for {}",
        agent_input.country,
    )

    container = get_container()
    adzuna = await container.resolve_provider(AppDependencies.adzuna_service)

    # Map to Service Schema
    params = AdzunaCategoriesParams(country=agent_input.country)

    try:
        response = await adzuna.get_categories(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna categories fetch failed",
        )
        return f"Error listing categories: {e}"

    if not response.results:
        return "No categories available"

    output = [f"Available Job Categories for {agent_input.country.upper()}:"]
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
    # Validate with Agent Schema
    agent_input = RegionalStatsInput(
        location=location,
        country=country,
    )

    logger.bind(
        location=agent_input.location,
        country=agent_input.country,
    ).info(
        "Fetching Adzuna regional stats for '{}' in {}",
        agent_input.location or "root",
        agent_input.country,
    )

    container = get_container()
    adzuna = await container.resolve_provider(AppDependencies.adzuna_service)

    # Map to Service Schema
    params = AdzunaGeodataParams(
        where=agent_input.location,
        country=agent_input.country,
    )

    try:
        response = await adzuna.get_geodata(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna geodata fetch failed",
        )
        return f"Error fetching regional stats: {e}"

    if not response.locations:
        return "No regional data available"

    output = [f"Regional Job Stats for '{agent_input.location or agent_input.country}':"]
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
    # Validate with Agent Schema
    agent_input = HistoricalTrendsInput(
        job_title=job_title,
        location=location,
        country=country,
        months=months,
    )

    logger.bind(
        job_title=agent_input.job_title,
        location=agent_input.location,
        months=agent_input.months,
    ).info(
        "Fetching Adzuna historical trends for '{}' in {} over {} months",
        agent_input.job_title,
        agent_input.location or "all locations",
        agent_input.months,
    )

    container = get_container()
    adzuna = await container.resolve_provider(AppDependencies.adzuna_service)

    # Map to Service Schema
    params = AdzunaHistoricalParams(
        what=agent_input.job_title,
        where=agent_input.location,
        country=agent_input.country,
        months=agent_input.months,
    )

    try:
        response = await adzuna.get_historical_data(params)
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception(
            "Adzuna historical data fetch failed",
        )
        return f"Error fetching historical trends: {e}"

    if not response.data:
        return f"No historical data available for: {agent_input.job_title}"

    output = [f"Historical Trends for '{agent_input.job_title}':"]
    output.append("")

    # Use the structured data property which merges month and count
    for point in response.data:
        salary_str = f"${point.average_salary:,.0f}" if point.average_salary else "N/A"
        output.append(
            f"- {point.month}: Average Salary: {salary_str}, Vacancies: {point.vacancy_count}",
        )

    return "\n".join(output)


__all__ = [
    "search_adzuna_jobs",
    "analyze_salary_trends",
    "get_top_hiring_companies",
    "list_job_categories",
    "get_regional_job_stats",
    "get_historical_salary_trends",
]
