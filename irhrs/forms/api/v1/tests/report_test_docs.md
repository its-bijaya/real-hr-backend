
# Table of Contents

1.  [Users:](#org1263ad7)
2.  [Test data will look as follows:](#org7e635b7)
    1.  [Section A](#orgc84f001)
        1.  [&rsquo;multiple-mcq&rsquo;](#orgd9d259f)
        2.  [&rsquo;single-mcq&rsquo;](#org3c09f80)
        3.  [&rsquo;short-text&rsquo;](#orgcd8af81)
        4.  [&rsquo;long-text&rsquo;](#org17fb3d3)
        5.  [&rsquo;rating-scale&rsquo;](#orgf4b377d)
    2.  [Section B](#orgb5120af)
        1.  [&rsquo;date&rsquo;](#orgcef9122)
        2.  [&rsquo;time&rsquo;](#org7e0ac12)
        3.  [&rsquo;duration&rsquo;](#org09d7d76)
        4.  [&rsquo;date-time&rsquo;](#orgda0251a)
        5.  [&rsquo;date-without-year&rsquo;](#orgcacd2a5)
        6.  [&rsquo;date-time-without-year&rsquo;](#org2b240d0)
        7.  [file-upload](#org60f53fb)
        8.  [multiple choice grid](#org119e04f)
        9.  [checkbox grid](#org079a5ee)



<a id="org1263ad7"></a>

# Users:

User A - Rajesh Shrestha
User B - Mahesh Manandhar
User C - Aayush Pudasaini


<a id="org7e635b7"></a>

# Test data will look as follows:


<a id="orgc84f001"></a>

## Section A


<a id="orgd9d259f"></a>

### &rsquo;multiple-mcq&rsquo;

(<sub>Question</sub>: Which of these places have you visited?\_)

**choices**:

-   Kathmandu - User A (Count: 1)
-   Bhaktapur - User B User C (Count: 2)
-   Lalitpur  - User A User B User C (Count 3)
-   Gorkha    - Blank (Count 0)


<a id="org3c09f80"></a>

### &rsquo;single-mcq&rsquo;

(<sub>Question</sub>: Choose one favorite food\_)

**choices**:

-   Ice-cream - User A (Count: 1)
-   Rice - User B User C (Count: 2)
-   Coffee - Blank (Count 0)


<a id="orgcd8af81"></a>

### &rsquo;short-text&rsquo;

(<sub>Question</sub>: What is your name?\_)


<a id="org17fb3d3"></a>

### &rsquo;long-text&rsquo;

(<sub>Question</sub>: Write a paragraph about the sun.\_)


<a id="orgf4b377d"></a>

### &rsquo;rating-scale&rsquo;

(<sub>Question</sub>: How much do you like chocolate?\_)

**choices**
1 (count: 0)
2 (count: 0)
3 (count: 2) (user A, B)
4 (count: 1) (user c)
5 (count: 0)


<a id="orgb5120af"></a>

## Section B


<a id="orgcef9122"></a>

### &rsquo;date&rsquo;

(<sub>Question</sub>: When did you last come to office?\_)

**choices**
2021-01-01 (count: 2) (User A, B)
2021-01-02 (count: 0)
2021-01-03 (count: 0)


<a id="org7e0ac12"></a>

### &rsquo;time&rsquo;

(<sub>Question</sub>: What time did you punch in at?\_)
 **choices**
5:30 (count 1) (User A)
5:31 (count 2) (User B C)


<a id="org09d7d76"></a>

### &rsquo;duration&rsquo;

(<sub>Question</sub>: How much time will it take to complete form reports?(in hr:min format)\_)
**choices**
23:40 (count 1) (User A)
23:40 (count 2) (User B C)


<a id="orgda0251a"></a>

### &rsquo;date-time&rsquo;

(<sub>Question</sub>: When does the world cup final start?\_)
**choices**
2021-01-01 05:40 (count 1) (User A)
2021-01-01 05:40 (count 1) (User B)


<a id="orgcacd2a5"></a>

### &rsquo;date-without-year&rsquo;

(<sub>Question</sub>: In which day did the last world cup final take place?\_)
**choices**
01-01 (count 1) (User A)
02-01 (count 1) (User B)


<a id="org2b240d0"></a>

### &rsquo;date-time-without-year&rsquo;

**choices**
(<sub>Question</sub>: In which day and time did the last world cup final take place?\_)
01-01 05:40 (count 1) (User B)
01-01 07:30 (count 1) (User C)


<a id="org60f53fb"></a>

### file-upload

(<sub>Question</sub>: Upload doctors appointment\_)


<a id="org119e04f"></a>

### multiple choice grid

(<sub>Question</sub>: Answer some questions about yourself.\_)

Rate the following people(choose only one):

    extra_data = {
        "rows": ["Ram", "Shyam", "Hari"],
        "columns": ["Wise", "Stupid", "Cool"]
    }

    answer_json = {
        "answers":  [
                ["Ram   ", ["Wise"],
                ["Shyam", ["Stupid"],
                ["Hari", ["Cool"],
            ]
    }

User A:

    {
        "answers": {
            "Ram": ["Wise"],
            "Shyam": ["Wise"],
            "Hari": []
        }
    },

User B:

    {
        "answers": {
            "Ram": ["Stupid"],
            "Shyam": ["Stupid"],
            "Hari": ["Stupid"]
        }
    },

User C:

    {
        "answers": {
            "Ram": [],
            "Shyam": [],
            "Hari": []
        }
    },


<a id="org079a5ee"></a>

### checkbox grid

Choices: Wise, Friendly, Communicative Stupid

Rate the following people:

    extra_data = {
        "rows": ["Ram", "Shyam", "Hari"],
        "columns": ["Wise", "Stupid", "Cool"],
        "all_rows_mandatory": True,
    }

User A

    {
        "answers": {
            "Ram": ["Wise", "Stupid", "Cool"],
            "Shyam": ["Wise", "Cool"],
            "Hari": ["Cool"],
        }
    },

User B:

    {
        "answers": {
            "Ram": ["Wise", "Stupid", "Cool"],
            "Shyam": ["Wise", "Stupid", "Cool"],
            "Hari": ["Wise", "Stupid", "Cool"],
        }
    },

User C:

    {
        "answers": {
            "Ram": [],
            "Shyam": [],
            "Hari": []
        }
    },

