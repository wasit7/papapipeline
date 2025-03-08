# **Chapter 1: Linux and Git Commands**

## **1.1 Linux Fundamentals**

### 1.1.1 Overview of the Linux File System
Linux is a **multiuser** operating system that organizes data in a hierarchical file system. The topmost directory is the **root**, denoted by `/`. Under the root directory, there are system directories like `/bin`, `/etc`, `/home`, etc.

Key points to remember:
- Almost **everything in Linux is a file**—including devices and directories.  
- **Home directories** (e.g., `/home/username`) are where users typically store their personal files.  

### 1.1.2 Directory Navigation
Navigating the file system is a fundamental skill in Linux.

- **`pwd`** (Print Working Directory)  
  Displays the absolute path of your current location. For example:
  ```bash
  pwd
  # Output: /home/jovyan/work
  ```
- **`ls`** (List)  
  Lists files and directories within the current or specified directory.
  ```bash
  ls
  # Output: Documents  Downloads  hello_flow.py ...
  ```
  - Common options:  
    - `ls -l` for a long listing (permissions, owner, size, modification date).  
    - `ls -a` to include hidden files (files starting with `.`).  
- **`cd <directory>`** (Change Directory)  
  Moves you from your current directory to `<directory>`.
  ```bash
  cd /home/jovyan/work
  ```

### 1.1.3 File Operations
Managing files and directories is at the core of Linux usage.

- **`cp <source> <destination>`** (Copy)  
  Copies the file(s) or directory(ies) from `<source>` to `<destination>`.  
  ```bash
  cp notes.txt backup_notes.txt
  ```
- **`mv <source> <destination>`** (Move/Rename)  
  Moves or renames `<source>` to `<destination>`. If `<destination>` is a directory, `<source>` is placed inside that directory.  
  ```bash
  mv old_name.txt new_name.txt
  ```
- **`rm <file>`** (Remove)  
  Deletes a file. Use `-r` (recursive) to remove a directory and its contents.  
  ```bash
  rm -r old_directory
  ```
  **Warning**: This permanently deletes files and directories, so be cautious.

- **`touch <filename>`**  
  Creates an empty file if it does not exist; otherwise, updates the file’s timestamp.  
  ```bash
  touch new_script.py
  ```

### 1.1.4 Permissions and Ownership
Linux enforces strict permissions for **users**, **groups**, and **others** to enhance security.

- **`chmod <permissions> <file>`**  
  Changes the permission bits of a file or directory. Permissions are represented as `r` (read), `w` (write), `x` (execute) or by numeric modes like `755`, `644`, etc.  
  ```bash
  chmod 755 my_script.sh
  ```
- **`chown <user>:<group> <file>`** (Change Ownership)  
  Changes the owner and group of the specified file or directory.  
  ```bash
  chown bob:developers project_folder
  ```

Understanding permissions is critical for controlling who can edit or execute scripts in multiuser environments.

---

## **1.2 Basic Git Workflow**

### 1.2.1 Introduction to Git
**Git** is a **distributed version control system** (DVCS) that tracks changes to files, facilitating collaboration and version tracking. Key Git concepts include:

- **Repository (repo)**: A collection of files tracked by Git.  
- **Commit**: A snapshot of changes at a certain point in time.  
- **Branch**: A parallel line of development, enabling multiple features or bug fixes to be developed simultaneously.

### 1.2.2 Initializing a Repository
To begin using Git locally on a new project:

- **`git init`**  
  Initializes a new, empty Git repository in the current directory. This creates a hidden `.git` folder.
  ```bash
  git init
  # Output: Initialized empty Git repository in /home/jovyan/work/my_project/.git/
  ```

### 1.2.3 Staging and Committing
Git separates **staging** (what changes will be included in your next commit) from **committing** (finalizing snapshots in the repository).

- **Staging**  
  - **`git add <file>`**: Adds a specific file to the staging area.  
  - **`git add .`**: Adds **all** modified and new files in the current directory.
- **Committing**  
  - **`git commit -m "Commit message"`**: Creates a new commit in the repository, storing the staged changes.  
    ```bash
    git add hello_flow.py
    git commit -m "Add initial flow definition"
    ```

### 1.2.4 Branching and Merging
Branches let you develop features independently of your main (production) branch.

- **Create a new branch**  
  ```bash
  git branch feature_x
  ```
- **Create a new branch(and switch to a new branch)**
  ```bash
  git checkout -b feature_x 
  # or
  git switch -c feature_x
  ```
- **Switch to a different branch**  
  ```bash
  git checkout feature_x
  # or
  git switch feature_x
  ```
- **Merging**  
  Once your feature is complete, merge it back into the main branch:
  ```bash
  git checkout main
  git merge feature_x
  ```

### 1.2.5 Working with Remotes
A **remote** refers to a version of the project hosted on the internet or network (e.g., GitHub).

- **`git remote -v`**  
  Lists the remote connections (URLs) for the repository. Often named `origin` by default.  
- **Pushing and Pulling**  
  - **`git push origin <branch>`**: Pushes local commits to the `<branch>` on the remote named `origin`.  
  - **`git pull origin <branch>`**: Fetches and merges remote changes into your local branch.  

---

## **1.3 Useful Commands and Tips**

### 1.3.1 Linux Utilities
- **`whoami`**: Displays the current logged-in username.  
- **`history`**: Lists your command history. You can re-run commands using `!<history-number>`.  
- **`grep <pattern> <file>`**: Searches for a pattern in a file.  
- **`head` / `tail`**: Shows the first or last lines of a file.

### 1.3.2 Common Git Commands
- **`git status`**: Shows current branch, staged vs unstaged changes.  
- **`git log --oneline`**: Displays the project’s commit history in a condensed format.  
- **`git revert <commit-hash>`**: Reverts a specific commit while preserving project history.  

### 1.3.3 SSH vs HTTPS for GitHub
- **SSH** is preferred because it doesn’t require you to enter your credentials every time and is more secure.  
- **HTTPS** can still be used, but typically you’ll need **Personal Access Tokens** since GitHub disabled password-based authentication for Git operations.

### 1.3.4 Best Practices
1. **Frequent Commits**: Commit changes often with clear messages to document your progress.  
2. **Use Branches**: Keep your main branch stable; do feature development on separate branches.  
3. **Regular Pulls**: Before pushing new changes, pull from the remote to minimize merge conflicts.  
4. **Meaningful Messages**: Write descriptive commit messages so others (and your future self) can understand what changed and why.

---

## **Summary**
In this chapter, you learned the basics of **navigating and managing files** in the Linux environment, as well as **version controlling** your projects with Git. Mastering these fundamentals lays the groundwork for the more advanced tasks of **containerization** (Chapter 2), **orchestration with Prefect** (Chapters 3 and 4), and **building end-to-end pipelines** (Chapter 5).

In the upcoming chapters, we will apply these Linux and Git concepts as we move on to **Docker**, **Docker Compose**, and the **Prefect** ecosystem to build robust data pipelines.

---

### **Key Takeaways**
- **Linux** organizes the file system hierarchically, and commands like `ls`, `cd`, `pwd` are essential for daily navigation.  
- **Git** is a distributed version control system; you can easily track changes and collaborate with others using branches and remote repositories.  
- **Staging and committing** are distinct steps in Git that provide flexibility and control over exactly which changes become part of your commit history.  
- **SSH authentication** is recommended for GitHub due to increased security and convenience.

With these topics understood, you’re prepared to move on to **Docker** and **Docker Compose** in the next chapter, where you’ll learn how to containerize and manage multi-service environments for your applications and data pipelines.
