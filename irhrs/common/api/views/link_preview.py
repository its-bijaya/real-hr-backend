import requests
from rest_framework import viewsets, response
from rest_framework.views import APIView
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class LinkPreview(APIView):
    def get(self, request, *args, **kwargs):
        url = request.query_params.get('url')

        # validates if url is supplied in query_params
        if(url == None):
            return response.Response({'data': None})

        # validates if url is valid
        url_validator = URLValidator(schemes=['http', 'https'])
        try:
            is_valid_url = url_validator(url)
        except ValidationError:
            return response.Response({'data': None})

        # obtaining full url host
        parsed = urlparse(url)
        host = parsed.hostname
        scheme = parsed.scheme
        full_host = scheme + '://' + host 
        
        # validates if url exists
        try:
            htmlResponse = requests.get(url)
        except requests.ConnectionError:
            return response.Response({'data': None})

        html = htmlResponse.text
        soup = BeautifulSoup(html)
        
        # obtain available page title
        ogTitle = soup.find("meta",  property="og:title")
        primaryTitle = ogTitle.get("content") if ogTitle else None
        secondaryTitle = soup.title.text if soup.title else None

        # obtain available page description
        ogDescription = soup.find("meta",  property="og:description")
        primaryDescription = ogDescription.get("content") if ogDescription else None
        description =  soup.find(attrs={'name':'description'})
        secondaryDescription = description.get("content") if description else None

        # obtain available display image
        ogImage = soup.find("meta",  property="og:image")
        primaryImage = ogImage.get("content") if ogImage else None
        images = soup.find_all('img')
        secondaryImage = soup.find_all('img')[0].get('src') if images else None
        imageUrl = primaryImage or secondaryImage
        
        return response.Response({
            'data': {
                'title': primaryTitle or secondaryTitle,
                'description': primaryDescription or secondaryDescription,
                'image': urljoin(full_host,imageUrl) if imageUrl else None
            }
        })
