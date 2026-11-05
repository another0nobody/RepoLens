package main

import "github.com/gin-gonic/gin"

func handleHealth(c *gin.Context) {
	c.JSON(200, gin.H{"ok": true})
}
