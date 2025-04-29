// FetchFox Script for ennvy.com UK Profiles
// Instructions:
// 1. Create a new FetchFox project
// 2. Paste this script into the script editor
// 3. Run the script

// Configuration
const BASE_URL = "https://www.ennvy.com";
const UK_LOCATIONS = [
    'wrexham', 'sevenoaks', 'bristol', 'manchester', 'birmingham',
    'slough', 'london', 'bromsgrove', 'sheffield', 'walton-on-thames',
    'hastings', 'london-', 'united-kingdom'
];
const MAX_PAGES_TO_SCRAPE = 3; // Per location
const DELAY_BETWEEN_REQUESTS = 2000; // 2 seconds

// Main function
async function main() {
    // Initialize results array
    let allResults = [];
    
    // Search through UK locations
    for (const location of UK_LOCATIONS) {
        log(`Searching location: ${location}`);
        
        let page = 1;
        let hasMorePages = true;
        
        while (hasMorePages && page <= MAX_PAGES_TO_SCRAPE) {
            const searchUrl = `${BASE_URL}/maleprofile/${location}/?page=${page}`;
            log(`Fetching page ${page}: ${searchUrl}`);
            
            try {
                await delay(DELAY_BETWEEN_REQUESTS);
                const response = await fetch(searchUrl, {
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                });
                
                if (!response.ok) {
                    log(`Failed to fetch page ${page} for ${location}`);
                    hasMorePages = false;
                    continue;
                }
                
                const html = await response.text();
                const profileLinks = extractProfileLinks(html, location);
                
                if (profileLinks.length === 0) {
                    hasMorePages = false;
                    continue;
                }
                
                // Process each profile
                for (const profileUrl of profileLinks) {
                    try {
                        await delay(DELAY_BETWEEN_REQUESTS);
                        const profileData = await scrapeProfilePage(profileUrl);
                        if (profileData) {
                            allResults.push(profileData);
                            log(`Found profile: ${profileData.username}`);
                        }
                    } catch (error) {
                        log(`Error scraping profile ${profileUrl}: ${error.message}`);
                    }
                }
                
                page++;
            } catch (error) {
                log(`Error fetching page ${page} for ${location}: ${error.message}`);
                hasMorePages = false;
            }
        }
    }
    
    // Save results
    if (allResults.length > 0) {
        const csvContent = convertToCSV(allResults);
        downloadCSV(csvContent, 'ennvy_uk_profiles.csv');
        log(`Successfully saved ${allResults.length} profiles to CSV`);
    } else {
        log('No profiles found');
    }
    
    return allResults;
}

// Helper functions
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function extractProfileLinks(html, location) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const links = Array.from(doc.querySelectorAll('a[href*="/maleprofile/"]'));
    
    const profileLinks = [];
    for (const link of links) {
        const href = link.getAttribute('href');
        if (href && href.includes(location)) {
            const fullUrl = href.startsWith('http') ? href : `${BASE_URL}${href}`;
            profileLinks.push(fullUrl);
        }
    }
    
    return [...new Set(profileLinks)]; // Remove duplicates
}

async function scrapeProfilePage(url) {
    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Extract username from URL
        const username = url.split('/').filter(Boolean).pop() || url.split('/').slice(-2, -1)[0];
        
        // Extract profile text
        const profileText = doc.body.textContent.replace(/\s+/g, ' ').trim();
        
        // Extract contact info
        const emails = extractEmails(profileText);
        const phones = extractPhones(profileText);
        
        // Extract profile details
        const title = doc.querySelector('h1')?.textContent.trim() || '';
        const location = doc.querySelector('.location, [class*="location"]')?.textContent.trim() || '';
        
        return {
            url,
            username,
            title,
            location,
            emails: [...new Set(emails)], // Remove duplicates
            phones: [...new Set(phones)],  // Remove duplicates
            scrapedAt: new Date().toISOString()
        };
    } catch (error) {
        log(`Error scraping profile page ${url}: ${error.message}`);
        return null;
    }
}

function extractEmails(text) {
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    return text.match(emailRegex) || [];
}

function extractPhones(text) {
    const phoneRegex = /(\+44|0)[\s-]?\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4}/g;
    return text.match(phoneRegex) || [];
}

function convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const rows = data.map(obj => headers.map(header => {
        const value = obj[header];
        if (Array.isArray(value)) {
            return value.join('; ');
        }
        return `"${String(value).replace(/"/g, '""')}"`;
    }).join(','));
    
    return [headers.join(','), ...rows].join('\n');
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Run the script
main().catch(error => log(`Script error: ${error.message}`));
