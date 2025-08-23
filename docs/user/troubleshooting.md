# Troubleshooting

Common issues and solutions for Holdem CLI.

## Installation Issues

### Command not found after installation

If `holdem` command is not available after installation:

**Solution**: Make sure your Python scripts directory is in your PATH:

```bash
# Add to your shell profile
export PATH="$HOME/.local/bin:$PATH"
```

### Permission denied errors

**Solution**: Install with user permissions:

```bash
pip install --user holdem-cli
```

## Common Runtime Issues

### "Profile not found" error

**Solution**: Initialize your profile first:

```bash
holdem init --profile yourname
```

### Database errors

**Solution**: Reset your local database:

```bash
# Backup existing data (optional)
cp -r ~/Library/Application\ Support/holdem-cli ~/Library/Application\ Support/holdem-cli-backup

# Reset database
rm -rf ~/Library/Application\ Support/holdem-cli/
holdem init --profile yourname
```

### Slow performance

**Solutions**:

1. **For equity calculations**: Use fewer iterations:
   ```bash
   holdem equity AKs QQ --iterations 10000
   ```

2. **For quizzes**: Reduce question count:
   ```bash
   holdem quiz hand-ranking --count 5
   ```

3. **Check system resources**: Close other applications using significant CPU/memory

## Quiz-Specific Issues

### Quiz difficulty not changing

**Problem**: Quiz difficulty stays the same despite good performance

**Solution**: The adaptive system requires several quiz sessions to learn your skill level. Try:
- Complete at least 3-5 quiz sessions
- Mix different quiz types (hand ranking, pot odds)
- Use consistent profile names

### Questions repeating too often

**Solution**: Increase the question pool by:
- Using different difficulty levels
- Mixing quiz types
- Waiting for the system to learn your preferences

## Simulation Issues

### AI opponents too difficult/easy

**Solution**: Choose appropriate AI level:

```bash
# For beginners
holdem simulate --ai easy

# For intermediate players
holdem simulate --ai medium

# For advanced practice
holdem simulate --ai hard
```

### Simulation not starting

**Problem**: Hand simulation fails to start

**Solution**:
1. Ensure you have initialized a profile
2. Check available memory
3. Try restarting the application

## Chart-Related Issues

### Chart import fails

**Problem**: Cannot import chart files

**Solutions**:
1. Check file format (should be JSON, CSV, or TXT)
2. Verify file permissions
3. Ensure file is not corrupted

### Chart display issues

**Problem**: Charts not displaying correctly

**Solution**: Reset chart view:
```bash
holdem charts view sample --reset
```

## Export/Import Issues

### Export files not found

**Solution**: Check export directory permissions and available disk space

### Import data corrupted

**Solution**: Use backup files or re-export from source

## Performance Optimization

### For slower computers

```bash
# Reduce equity calculation iterations
holdem equity AKs QQ --iterations 5000

# Use simpler chart views
holdem charts view sample --simple

# Limit quiz question count
holdem quiz hand-ranking --count 3
```

### Memory usage issues

**Solution**:
1. Close unused applications
2. Restart Holdem CLI between long sessions
3. Use `--simple` flag for chart operations

## Getting Help

If you continue to experience issues:

1. **Check the logs**: Look for error messages in terminal output
2. **Update the application**: `pip install --upgrade holdem-cli`
3. **Report issues**: [GitHub Issues](https://github.com/dylanchidambaram/holdem-cli/issues)
4. **Check documentation**: Review this troubleshooting guide and [user guide](guide.md)

## Diagnostic Commands

Use these commands to gather diagnostic information:

```bash
# Check version
holdem --version

# Get help for any command
holdem quiz --help
holdem simulate --help

# Check profile status
holdem profile stats yourname
```
